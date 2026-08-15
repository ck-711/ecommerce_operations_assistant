import hashlib, json, os, sqlite3, threading, time, uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROOT=os.path.dirname(os.path.abspath(__file__)); DB=os.path.join(ROOT,'ecommerce.db'); TOKENS={}; LOCK=threading.Lock()
def now(): return datetime.now(timezone.utc).isoformat()
def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); return c
def init():
    c=db()
    with open(os.path.join(ROOT,'schema.sql'),encoding='utf-8') as f: c.executescript(f.read())
    if not c.execute('select 1 from users limit 1').fetchone():
        for u,r in [('admin','admin'),('operator','operator'),('viewer','viewer')]: c.execute('insert into users(username,display_name,password_hash,role) values(?,?,?,?)',(u,u,hashlib.sha256((u+'123').encode()).hexdigest(),r))
    c.commit(); c.close()
def rows(c,sql,args=()): return [dict(x) for x in c.execute(sql,args).fetchall()]
def one(c,sql,args=()):
    x=c.execute(sql,args).fetchone(); return dict(x) if x else None
def jdump(x): return json.dumps(x,ensure_ascii=False)
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def send(self,status,data,ctype='application/json'):
        raw=data if isinstance(data,bytes) else (json.dumps(data,ensure_ascii=False).encode() if ctype=='application/json' else data.encode()); self.send_response(status); self.send_header('Content-Type',ctype+'; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def body(self):
        n=int(self.headers.get('Content-Length','0')); return json.loads(self.rfile.read(n) or '{}')
    def auth(self,write=False):
        t=self.headers.get('Authorization','').replace('Bearer ',''); u=TOKENS.get(t)
        if not u: self.send(401,{'code':'unauthorized','message':'请先登录','details':{}}); return None
        if write and u['role']=='viewer': self.send(403,{'code':'forbidden','message':'查看人员无写权限','details':{}}); return None
        return u
    def do_GET(self):
        p=urlparse(self.path).path
        if p=='/' or p=='/index.html': return self.send(200,open(os.path.join(ROOT,'web','index.html'),encoding='utf-8').read(),'text/html')
        if p.startswith('/web/'): return self.send(200,open(os.path.join(ROOT,p[1:]),encoding='utf-8').read(), 'text/css' if p.endswith('.css') else 'text/javascript')
        u=self.auth();
        if not u:return
        c=db()
        if p=='/api/v1/auth/me': out=u
        elif p=='/api/v1/stores': out=rows(c,'select * from stores order by id desc')
        elif p=='/api/v1/products': out=rows(c,'select p.*,s.store_name from products p join stores s on s.id=p.store_id order by p.id desc')
        elif p.startswith('/api/v1/products/'):
            pid=p.split('/')[4]; out=one(c,'select * from products where id=?',(pid,))
            if out: out['competitors']=rows(c,'select * from competitors where product_id=?',(pid,)); out['diagnoses']=rows(c,'select * from product_diagnoses where product_id=? order by id desc',(pid,)); out['plans']=rows(c,'select * from creative_plans where product_id=? order by id desc',(pid,)); out['jobs']=rows(c,'select * from generation_jobs where product_id=? order by id desc',(pid,)); out['performance']=rows(c,'select * from performance_records where product_id=? order by id desc',(pid,)); out['reports']=rows(c,'select * from review_reports where product_id=? order by id desc',(pid,))
        else: out={'code':'not_found','message':'资源不存在','details':{}}
        c.close(); self.send(200 if not isinstance(out,dict) or 'code' not in out else 404,out)
    def do_POST(self):
        p=urlparse(self.path).path; data=self.body()
        if p=='/api/v1/auth/login':
            c=db(); u=one(c,'select * from users where username=? and status="active"',(data.get('username'),)); c.close()
            if not u or u['password_hash']!=hashlib.sha256(str(data.get('password','')).encode()).hexdigest(): return self.send(401,{'code':'invalid_credentials','message':'用户名或密码错误','details':{}})
            t=uuid.uuid4().hex; TOKENS[t]=u; return self.send(200,{'access_token':t,'token_type':'bearer','user':u})
        u=self.auth(True)
        if not u:return
        c=db(); t=now(); out=None; status=201
        if p=='/api/v1/workspace/demo-data':
            c.execute('insert into stores(store_name,platform,owner_name,remark,created_at,updated_at) values(?,?,?,?,?,?)',('演示旗舰店','taobao','演示运营','MVP demo',t,t)); sid=c.execute('select last_insert_rowid()').fetchone()[0]; c.execute('insert into products(store_id,name,platform,category,price,cost,target_audience,selling_points,status,created_at,updated_at) values(?,?,?,?,?,?,?,?,?,?,?)',(sid,'轻量防晒伞','taobao','户外用品',79,32,'通勤女性','轻量、遮阳、便携','active',t,t)); pid=c.execute('select last_insert_rowid()').fetchone()[0]; c.execute('insert into product_skus(product_id,sku_code,sku_name,price) values(?,?,?,?)',(pid,'SKU-DEMO','黑色/标准',79)); sku=c.execute('select last_insert_rowid()').fetchone()[0]; c.execute('insert into inventory_items(sku_id,stock_qty,warning_threshold,updated_at) values(?,?,?,?)',(sku,42,10,t)); out={'store_id':sid,'product_id':pid}
        elif p=='/api/v1/stores': c.execute('insert into stores(store_name,platform,owner_name,remark,created_at,updated_at) values(?,?,?,?,?,?)',(data['store_name'],data.get('platform','other'),data.get('owner_name',''),data.get('remark',''),t,t)); out={'id':c.execute('select last_insert_rowid()').fetchone()[0]}
        elif p=='/api/v1/products': c.execute('insert into products(store_id,name,platform,category,price,cost,target_audience,selling_points,status,created_at,updated_at) values(?,?,?,?,?,?,?,?,?,?,?)',(data['store_id'],data['name'],data.get('platform','other'),data.get('category',''),data.get('price',0),data.get('cost',0),data.get('target_audience',''),data.get('selling_points',''),'draft',t,t)); out={'id':c.execute('select last_insert_rowid()').fetchone()[0]}
        elif p.endswith('/diagnoses/generate'):
            pid=p.split('/')[4]; d={'positioning':'高性价比通勤防晒单品','price_band':'50-99 元','audience_insights':'一二线城市通勤女性，重视便携与防晒','pain_points':'笨重、收纳不便、遮阳不足','selling_point_analysis':'轻量与便携是核心差异点','risks':'同质化、季节性波动','recommendations':'强化收纳演示，增加防晒效果对比'}; c.execute('insert into product_diagnoses(product_id,positioning,price_band,audience_insights,pain_points,selling_point_analysis,risks,recommendations,created_at,updated_at) values(?,?,?,?,?,?,?,?,?,?)',(pid,*d.values(),t,t)); out={'id':c.execute('select last_insert_rowid()').fetchone()[0],**d}
        elif '/creative-plans/' in p and p.endswith('/generate'):
            pid=p.split('/')[4]; typ=p.split('/')[6]; items=[{'方案标题':'通勤痛点对比','画面结构':'地铁口→展开→遮阳对比','核心文案':'轻到忘记带伞','突出卖点':'轻量便携','方案理由':'三秒展示使用价值'},{'方案标题':'包内收纳','画面结构':'手袋空间→收纳','核心文案':'随身不占地','突出卖点':'超薄收纳','方案理由':'降低携带顾虑'},{'方案标题':'防晒实测','画面结构':'阳光下左右对比','核心文案':'看得见的遮阳','突出卖点':'遮阳效果','方案理由':'用证据建立信任'}]; content=[dict(x,**({'开头钩子':'出门最怕什么？','镜头分镜':'3 个快切镜头','口播文案':'轻便防晒，通勤必备','转化引导':'点击了解'} if typ=='video-scripts' else {})) for x in items]; c.execute('insert into creative_plans(product_id,plan_type,title,content_json,created_at,updated_at) values(?,?,?,?,?,?)',(pid,typ,typ+' 方案',jdump(content),t,t)); out={'id':c.execute('select last_insert_rowid()').fetchone()[0],'plan_type':typ,'content':content}
        elif '/creative-plans/' in p and (p.endswith('/images/generate') or p.endswith('/videos/generate')):
            bits=p.split('/'); pid=bits[4]; plan_id=bits[6]; kind='image' if p.endswith('/images/generate') else 'video'; c.execute('insert into generation_jobs(product_id,creative_plan_id,job_kind,created_at) values(?,?,?,?)',(pid,plan_id,kind,t)); jid=c.execute('select last_insert_rowid()').fetchone()[0]; c.execute('insert into generation_job_events(job_id,event_type,event_message,created_at) values(?,?,?,?)',(jid,'queued','任务已入队',t)); out={'id':jid,'job_status':'pending'}
        elif '/generation-jobs/' in p and p.endswith('/retry'):
            jid=p.split('/')[6]; c.execute('update generation_jobs set job_status="pending",error_message=NULL where id=? and job_status in ("failed","timeout")',(jid,)); out={'id':int(jid),'job_status':'pending'}
        elif '/generation-jobs/' in p and p.endswith('/cancel'):
            jid=p.split('/')[6]; c.execute('update generation_jobs set job_status="cancelled",finished_at=? where id=? and job_status in ("pending","running")',(t,jid)); out={'id':int(jid),'job_status':'cancelled'}
        elif p.endswith('/performance-records'):
            pid=p.split('/')[4]; c.execute('insert into performance_records(product_id,period_start,period_end,impressions,clicks,conversions,spend,revenue,notes,created_at) values(?,?,?,?,?,?,?,?,?,?)',(pid,data['period_start'],data['period_end'],data.get('impressions',0),data.get('clicks',0),data.get('conversions',0),data.get('spend',0),data.get('revenue',0),data.get('notes',''),t)); out={'id':c.execute('select last_insert_rowid()').fetchone()[0]}
        elif p.endswith('/review-reports/generate'):
            pid=p.split('/')[4]; rec=one(c,'select coalesce(sum(impressions),0) impressions,coalesce(sum(clicks),0) clicks,coalesce(sum(conversions),0) conversions,coalesce(sum(spend),0) spend,coalesce(sum(revenue),0) revenue,min(period_start) period_start,max(period_end) period_end from performance_records where product_id=?',(pid,)); ctr=(rec['clicks']/rec['impressions'] if rec['impressions'] else 0); roi=(rec['revenue']/rec['spend'] if rec['spend'] else 0); summary=f"累计曝光 {rec['impressions']}，点击 {rec['clicks']}，转化 {rec['conversions']}，CTR {ctr:.2%}，ROI {roi:.2f}"; c.execute('insert into review_reports(product_id,period_start,period_end,summary_text,insights_json,next_actions_json,created_at) values(?,?,?,?,?,?,?)',(pid,rec['period_start'],rec['period_end'],summary,jdump(['关注点击到转化的漏斗损耗']),jdump(['测试防晒实测主图','补充高意向人群素材']),t)); out={'id':c.execute('select last_insert_rowid()').fetchone()[0],'summary_text':summary}
        else: out={'code':'not_found','message':'接口不存在','details':{}}; status=404
        c.commit(); c.close(); self.send(status,out)
def worker():
    while True:
        c=db(); jobs=rows(c,'select * from generation_jobs where job_status="pending"');
        for j in jobs:
            c.execute('update generation_jobs set job_status="running",started_at=? where id=?',(now(),j['id'])); c.execute('insert into generation_job_events(job_id,event_type,event_message,created_at) values(?,?,?,?)',(j['id'],'running','任务开始执行',now())); c.commit(); time.sleep(.15); c.execute('update generation_jobs set job_status="succeeded",finished_at=?,result_json=? where id=?',(now(),jdump({'asset_url':'/demo-assets/'+str(j['id'])+'.png'}),j['id'])); c.execute('insert into generation_job_events(job_id,event_type,event_message,created_at) values(?,?,?,?)',(j['id'],'succeeded','演示素材已生成',now())); c.commit()
        c.close(); time.sleep(1)
if __name__=='__main__':
    init(); threading.Thread(target=worker,daemon=True).start(); print('Ecommerce assistant: http://127.0.0.1:8000'); ThreadingHTTPServer(('127.0.0.1',8000),Handler).serve_forever()
