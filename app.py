import csv, hashlib, io, json, os, sqlite3, threading, time, uuid
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
def import_rows(kind,text,c):
    required={'products':['store_id','name'],'sku-inventory':['product_id','sku_code','sku_name'],'performance-records':['product_id','period_start','period_end']}[kind]; parsed=[]; errors=[]
    for i,row in enumerate(csv.DictReader(io.StringIO(text)),2):
        miss=[x for x in required if not row.get(x)]
        try:
            if kind=='products' and row.get('store_id') and not one(c,'select id from stores where id=?',(row['store_id'],)): miss.append('store_id 不存在')
            if kind=='sku-inventory' and row.get('product_id') and not one(c,'select id from products where id=?',(row['product_id'],)): miss.append('product_id 不存在')
            for k in ('price','cost','stock_qty','warning_threshold','impressions','clicks','conversions','spend','revenue'):
                if row.get(k): float(row[k])
        except ValueError: miss.append('数值字段格式错误')
        (errors if miss else parsed).append({'row':i,'data':row,'errors':miss} if miss else row)
    return parsed,errors
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
        elif p=='/api/v1/users':
            if u['role']!='admin': out={'code':'forbidden','message':'仅管理员可查看用户','details':{}}
            else: out=rows(c,'select id,username,display_name,role,status from users order by id')
        elif p=='/api/v1/workspace/dashboard': out={'stores':c.execute('select count(*) n from stores').fetchone()['n'],'products':c.execute('select count(*) n from products').fetchone()['n'],'low_stock_skus':c.execute('select count(*) n from inventory_items where stock_qty<=warning_threshold').fetchone()['n'],'pending_assets':c.execute('select count(*) n from generated_assets where review_status="pending"').fetchone()['n']}
        elif p=='/api/v1/stores': out=rows(c,'select * from stores order by id desc')
        elif p.startswith('/api/v1/stores/'):
            sid=p.split('/')[4]; out=one(c,'select * from stores where id=?',(sid,))
            if out: out['products']=rows(c,'select * from products where store_id=?',(sid,)); out['low_stock_skus']=rows(c,'select k.sku_code,k.sku_name,i.stock_qty,i.warning_threshold from product_skus k join products p on p.id=k.product_id join inventory_items i on i.sku_id=k.id where p.store_id=? and i.stock_qty<=i.warning_threshold',(sid,)); out['product_count']=len(out['products'])
        elif p=='/api/v1/products': out=rows(c,'select p.*,s.store_name from products p join stores s on s.id=p.store_id order by p.id desc')
        elif p.startswith('/api/v1/products/'):
            pid=p.split('/')[4]; out=one(c,'select * from products where id=?',(pid,))
            if out:
                out['competitors']=rows(c,'select * from competitors where product_id=?',(pid,)); out['diagnoses']=rows(c,'select * from product_diagnoses where product_id=? order by id desc',(pid,)); out['plans']=rows(c,'select * from creative_plans where product_id=? order by id desc',(pid,)); out['jobs']=rows(c,'select * from generation_jobs where product_id=? order by id desc',(pid,));
                for j in out['jobs']: j['events']=rows(c,'select * from generation_job_events where job_id=? order by id',(j['id'],))
                out['skus']=rows(c,'select k.*,coalesce(i.stock_qty,0) stock_qty,coalesce(i.locked_qty,0) locked_qty,coalesce(i.warning_threshold,10) warning_threshold,(coalesce(i.stock_qty,0)<=coalesce(i.warning_threshold,10)) low_stock from product_skus k left join inventory_items i on i.sku_id=k.id where k.product_id=? order by k.id',(pid,)); out['inventory_movements']=rows(c,'select m.* from inventory_movements m join product_skus k on k.id=m.sku_id where k.product_id=? order by m.id desc',(pid,)); out['links']=rows(c,'select * from promotion_links where product_id=? order by id desc',(pid,)); out['ad_recommendations']=rows(c,'select * from ad_recommendations where product_id=? order by id desc',(pid,)); out['ad_experiments']=rows(c,'select * from ad_experiments where product_id=? order by id desc',(pid,)); out['assets']=rows(c,'select * from generated_assets where product_id=? order by id desc',(pid,)); out['performance']=rows(c,'select * from performance_records where product_id=? order by id desc',(pid,)); out['reports']=rows(c,'select * from review_reports where product_id=? order by id desc',(pid,))
        else: out={'code':'not_found','message':'资源不存在','details':{}}
        c.close(); self.send(200 if not isinstance(out,dict) or 'code' not in out else ({'forbidden':403,'not_found':404}.get(out.get('code'),400)),out)
    def do_POST(self):
        p=urlparse(self.path).path; data=self.body()
        if p=='/api/v1/auth/login':
            c=db(); u=one(c,'select * from users where username=? and status="active"',(data.get('username'),)); c.close()
            if not u or u['password_hash']!=hashlib.sha256(str(data.get('password','')).encode()).hexdigest(): return self.send(401,{'code':'invalid_credentials','message':'用户名或密码错误','details':{}})
            t=uuid.uuid4().hex; TOKENS[t]=u; return self.send(200,{'access_token':t,'token_type':'bearer','user':u})
        u=self.auth(True)
        if not u:return
        c=db(); t=now(); out=None; status=201
        if p.startswith('/api/v1/workspace/imports/'):
            bits=p.split('/'); kind=bits[5]; mode=bits[6]; parsed,errors=import_rows(kind,str(data.get('csv_text','')),c)
            if mode=='preview': out={'valid_rows':len(parsed),'error_rows':len(errors),'errors':errors}; status=200
            elif mode=='commit':
                success=0; commit_errors=list(errors)
                for row in parsed:
                    try:
                        if kind=='products': c.execute('insert into products(store_id,name,platform,category,price,cost,target_audience,selling_points,status,created_at,updated_at) values(?,?,?,?,?,?,?,?,?,?,?)',(row['store_id'],row['name'],row.get('platform','other'),row.get('category',''),float(row.get('price') or 0),float(row.get('cost') or 0),row.get('target_audience',''),row.get('selling_points',''),'draft',t,t))
                        elif kind=='sku-inventory':
                            if one(c,'select id from product_skus where product_id=? and sku_code=?',(row['product_id'],row['sku_code'])): raise ValueError('SKU 编码已存在')
                            c.execute('insert into product_skus(product_id,sku_code,sku_name,price) values(?,?,?,?)',(row['product_id'],row['sku_code'],row['sku_name'],float(row.get('price') or 0))); sid=c.execute('select last_insert_rowid()').fetchone()[0]; c.execute('insert into inventory_items(sku_id,stock_qty,warning_threshold,updated_at) values(?,?,?,?)',(sid,int(float(row.get('stock_qty') or 0)),int(float(row.get('warning_threshold') or 10)),t))
                        else: c.execute('insert into performance_records(product_id,period_start,period_end,impressions,clicks,conversions,spend,revenue,notes,created_at) values(?,?,?,?,?,?,?,?,?,?)',(row['product_id'],row['period_start'],row['period_end'],int(float(row.get('impressions') or 0)),int(float(row.get('clicks') or 0)),int(float(row.get('conversions') or 0)),float(row.get('spend') or 0),float(row.get('revenue') or 0),row.get('notes',''),t))
                        success+=1
                    except (ValueError,sqlite3.IntegrityError) as e: commit_errors.append({'row':row.get('row','?'),'data':row,'errors':[str(e)]})
                out={'success_count':success,'error_count':len(commit_errors),'errors':commit_errors}; status=200
            else: out={'code':'not_found','message':'导入模式不存在','details':{}}; status=404
        elif p=='/api/v1/workspace/demo-data':
            c.execute('insert into stores(store_name,platform,owner_name,remark,created_at,updated_at) values(?,?,?,?,?,?)',('演示旗舰店','taobao','演示运营','MVP demo',t,t)); sid=c.execute('select last_insert_rowid()').fetchone()[0]; c.execute('insert into products(store_id,name,platform,category,price,cost,target_audience,selling_points,status,created_at,updated_at) values(?,?,?,?,?,?,?,?,?,?,?)',(sid,'轻量防晒伞','taobao','户外用品',79,32,'通勤女性','轻量、遮阳、便携','active',t,t)); pid=c.execute('select last_insert_rowid()').fetchone()[0]; c.execute('insert into product_skus(product_id,sku_code,sku_name,price) values(?,?,?,?)',(pid,'SKU-DEMO','黑色/标准',79)); sku=c.execute('select last_insert_rowid()').fetchone()[0]; c.execute('insert into inventory_items(sku_id,stock_qty,warning_threshold,updated_at) values(?,?,?,?)',(sku,42,10,t)); out={'store_id':sid,'product_id':pid}
            c.execute('insert into competitors(product_id,name,platform,url,price,selling_points,created_at) values(?,?,?,?,?,?,?)',(pid,'竞品轻便伞','taobao','https://example.com/item',69,'轻量、防晒',t)); c.execute('insert into product_diagnoses(product_id,positioning,price_band,audience_insights,pain_points,selling_point_analysis,risks,recommendations,created_at,updated_at) values(?,?,?,?,?,?,?,?,?,?)',(pid,'高性价比通勤防晒单品','50-99 元','通勤女性','笨重、收纳不便','轻量便携差异化','同质化风险','强化实测对比',t,t)); c.execute('insert into creative_plans(product_id,plan_type,title,content_json,created_at,updated_at) values(?,?,?,?,?,?)',(pid,'main-images','演示主图方案',jdump([{'方案标题':'通勤对比','画面结构':'地铁口→展开','核心文案':'轻到忘记带伞'}]),t,t)); c.execute('insert into performance_records(product_id,period_start,period_end,impressions,clicks,conversions,spend,revenue,notes,created_at) values(?,?,?,?,?,?,?,?,?,?)',(pid,'2026-08-01','2026-08-15',10000,420,32,800,2560,'演示数据',t)); c.execute('insert into review_reports(product_id,period_start,period_end,summary_text,insights_json,next_actions_json,created_at) values(?,?,?,?,?,?,?)',(pid,'2026-08-01','2026-08-15','演示周期 ROI 3.2','["点击率稳定"]','["测试新主图"]',t))
        elif p=='/api/v1/stores': c.execute('insert into stores(store_name,platform,owner_name,remark,created_at,updated_at) values(?,?,?,?,?,?)',(data['store_name'],data.get('platform','other'),data.get('owner_name',''),data.get('remark',''),t,t)); out={'id':c.execute('select last_insert_rowid()').fetchone()[0]}
        elif p=='/api/v1/products': c.execute('insert into products(store_id,name,platform,category,price,cost,target_audience,selling_points,status,created_at,updated_at) values(?,?,?,?,?,?,?,?,?,?,?)',(data['store_id'],data['name'],data.get('platform','other'),data.get('category',''),data.get('price',0),data.get('cost',0),data.get('target_audience',''),data.get('selling_points',''),'draft',t,t)); out={'id':c.execute('select last_insert_rowid()').fetchone()[0]}
        elif p.endswith('/skus') and '/products/' in p:
            pid=p.split('/')[4]
            if one(c,'select id from products where id=?',(pid,)) is None: out={'code':'not_found','message':'商品不存在','details':{}}; status=404
            elif not data.get('sku_code') or not data.get('sku_name'): out={'code':'validation_error','message':'SKU 编码和名称不能为空','details':{}}; status=400
            elif one(c,'select id from product_skus where product_id=? and sku_code=?',(pid,data['sku_code'])): out={'code':'conflict','message':'SKU 编码已存在','details':{}}; status=409
            else:
                c.execute('insert into product_skus(product_id,sku_code,sku_name,price,status) values(?,?,?,?,?)',(pid,data['sku_code'],data['sku_name'],data.get('price',0),data.get('status','active'))); sid=c.execute('select last_insert_rowid()').fetchone()[0]; c.execute('insert into inventory_items(sku_id,stock_qty,warning_threshold,updated_at) values(?,?,?,?)',(sid,int(data.get('stock_qty',0)),int(data.get('warning_threshold',10)),t)); out={'id':sid,'sku_code':data['sku_code'],'stock_qty':int(data.get('stock_qty',0))}
        elif p.endswith('/inventory-adjustments'):
            bits=p.split('/'); pid,sid=bits[4],bits[6]; sku=one(c,'select k.*,coalesce(i.stock_qty,0) stock_qty from product_skus k left join inventory_items i on i.sku_id=k.id where k.id=? and k.product_id=?',(sid,pid)); change=data.get('change_qty'); reason=str(data.get('reason_text','')).strip()
            if not sku: out={'code':'not_found','message':'SKU 不存在','details':{}}; status=404
            elif not isinstance(change,int) or not reason: out={'code':'validation_error','message':'变更数量必须为整数且原因不能为空','details':{}}; status=400
            elif sku['stock_qty']+change<0: out={'code':'validation_error','message':'库存不能小于 0','details':{}}; status=400
            else:
                after=sku['stock_qty']+change; c.execute('update inventory_items set stock_qty=?,updated_at=? where sku_id=?',(after,t,sid)); c.execute('insert into inventory_movements(sku_id,movement_type,change_qty,before_qty,after_qty,reason_text,created_at) values(?,?,?,?,?,?,?)',(sid,'adjustment',change,sku['stock_qty'],after,reason,t)); out={'sku_id':int(sid),'before_qty':sku['stock_qty'],'after_qty':after}
        elif p.endswith('/competitors'):
            pid=p.split('/')[4]; c.execute('insert into competitors(product_id,name,platform,url,price,selling_points,created_at) values(?,?,?,?,?,?,?)',(pid,data['name'],data.get('platform','other'),data.get('url',''),data.get('price'),data.get('selling_points',''),t)); out={'id':c.execute('select last_insert_rowid()').fetchone()[0]}
        elif p.endswith('/promotion-links/generate'):
            out={'link_name':data.get('link_name','商品推广链接'),'target_url':data.get('target_url',''),'scene_text':data.get('scene_text','内容投放'),'utm':{'source':'ecommerce-assistant','medium':'demo','campaign':'product-'+p.split('/')[4]}}
        elif p.endswith('/promotion-links'):
            pid=p.split('/')[4]; code=uuid.uuid4().hex[:10]; c.execute('insert into promotion_links(product_id,link_name,target_url,tracking_code,scene_text,created_at) values(?,?,?,?,?,?)',(pid,data['link_name'],data['target_url'],code,data.get('scene_text',''),t)); out={'id':c.execute('select last_insert_rowid()').fetchone()[0],'tracking_code':code}
        elif p.endswith('/ad-recommendations/generate'):
            pid=p.split('/')[4]; rec={'summary_text':'先小预算测试高意向通勤人群，再根据转化扩量','objective_text':'提升商品详情页转化','audience_segments':['通勤女性','户外出行人群'],'budget_plan':{'daily':100,'test_days':3},'confirm_status':'pending'}; c.execute('insert into ad_recommendations(product_id,summary_text,objective_text,audience_segments_json,budget_plan_json,created_at) values(?,?,?,?,?,?)',(pid,rec['summary_text'],rec['objective_text'],jdump(rec['audience_segments']),jdump(rec['budget_plan']),t)); out={'id':c.execute('select last_insert_rowid()').fetchone()[0],**rec}
        elif p.endswith('/platform-accounts'):
            sid=p.split('/')[4]; c.execute('insert into platform_accounts(store_id,platform,account_name,auth_status,auth_meta_json,remark,created_at,updated_at) values(?,?,?,?,?,?,?,?)',(sid,data['platform'],data['account_name'],'not_connected',jdump({'provider':'placeholder'}),data.get('remark',''),t,t)); out={'id':c.execute('select last_insert_rowid()').fetchone()[0],'auth_status':'not_connected'}
        elif p.endswith('/ad-experiments'):
            pid=p.split('/')[4]; c.execute('insert into ad_experiments(product_id,experiment_name,target_text,audience_text,budget_amount,success_metric_text,hypothesis_text,created_at,updated_at) values(?,?,?,?,?,?,?,?,?)',(pid,data['experiment_name'],data.get('target_text',''),data.get('audience_text',''),data.get('budget_amount',0),data.get('success_metric_text',''),data.get('hypothesis_text',''),t,t)); out={'id':c.execute('select last_insert_rowid()').fetchone()[0],'experiment_status':'draft'}
        elif p.endswith('/diagnoses/generate'):
            pid=p.split('/')[4]; d={'positioning':'高性价比通勤防晒单品','price_band':'50-99 元','audience_insights':'一二线城市通勤女性，重视便携与防晒','pain_points':'笨重、收纳不便、遮阳不足','selling_point_analysis':'轻量与便携是核心差异点','risks':'同质化、季节性波动','recommendations':'强化收纳演示，增加防晒效果对比'}; c.execute('insert into product_diagnoses(product_id,positioning,price_band,audience_insights,pain_points,selling_point_analysis,risks,recommendations,created_at,updated_at) values(?,?,?,?,?,?,?,?,?,?)',(pid,*d.values(),t,t)); out={'id':c.execute('select last_insert_rowid()').fetchone()[0],**d}
        elif '/creative-plans/' in p and p.endswith('/generate') and not (p.endswith('/images/generate') or p.endswith('/videos/generate')):
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
    def do_PATCH(self):
        p=urlparse(self.path).path; data=self.body(); u=self.auth(True)
        if not u:return
        c=db(); t=now(); out=None; status=200
        if '/ad-recommendations/' in p and p.endswith('/confirmation'):
            bits=p.split('/'); pid,rid=bits[4],bits[6]; status_value=data.get('confirm_status'); rec=one(c,'select * from ad_recommendations where id=? and product_id=?',(rid,pid))
            if not rec: out={'code':'not_found','message':'投放建议不存在','details':{}}; status=404
            elif status_value not in ('confirmed','rejected'): out={'code':'validation_error','message':'确认状态无效','details':{}}; status=400
            else: c.execute('update ad_recommendations set confirm_status=? where id=?',(status_value,rid)); out={'id':int(rid),'confirm_status':status_value}
        elif '/ad-experiments/' in p:
            bits=p.split('/'); pid,eid=bits[4],bits[6]; exp=one(c,'select * from ad_experiments where id=? and product_id=?',(eid,pid)); new_status=data.get('experiment_status')
            allowed={'draft':('confirmed','cancelled'),'confirmed':('running','cancelled'),'running':('finished','cancelled'),'finished':(),'cancelled':()}
            if not exp: out={'code':'not_found','message':'投放实验不存在','details':{}}; status=404
            elif new_status not in allowed.get(exp['experiment_status'],()): out={'code':'invalid_transition','message':'实验状态流转不允许','details':{'from':exp['experiment_status'],'to':new_status}}; status=400
            else: c.execute('update ad_experiments set experiment_status=?,updated_at=? where id=?',(new_status,t,eid)); out={'id':int(eid),'experiment_status':new_status}
        elif '/skus/' in p and '/assets/' not in p:
            bits=p.split('/'); pid,sid=bits[4],bits[6]; sku=one(c,'select * from product_skus where id=? and product_id=?',(sid,pid))
            if not sku: out={'code':'not_found','message':'SKU 不存在','details':{}}; status=404
            elif data.get('status') not in (None,'active','inactive') or ('price' in data and float(data['price'])<0) or ('warning_threshold' in data and int(data['warning_threshold'])<0): out={'code':'validation_error','message':'SKU 状态、价格或预警阈值无效','details':{}}; status=400
            else:
                c.execute('update product_skus set sku_name=coalesce(?,sku_name),price=coalesce(?,price),status=coalesce(?,status) where id=?',(data.get('sku_name'),data.get('price'),data.get('status'),sid));
                if 'warning_threshold' in data: c.execute('update inventory_items set warning_threshold=?,updated_at=? where sku_id=?',(int(data['warning_threshold']),t,sid))
                out=one(c,'select k.*,i.stock_qty,i.warning_threshold from product_skus k join inventory_items i on i.sku_id=k.id where k.id=?',(sid,))
        elif '/assets/' in p:
            bits=p.split('/'); pid,aid=bits[4],bits[6]; asset=one(c,'select * from generated_assets where id=? and product_id=?',(aid,pid))
            if not asset: out={'code':'not_found','message':'素材不存在','details':{}}; status=404
            elif data.get('review_status') not in (None,'pending','approved','rejected') or (data.get('score') is not None and not 0<=float(data['score'])<=5): out={'code':'validation_error','message':'审核状态或评分无效','details':{}}; status=400
            else:
                c.execute('update generated_assets set review_status=coalesce(?,review_status),score=coalesce(?,score),tags_json=coalesce(?,tags_json),remark=coalesce(?,remark),usage_scene=coalesce(?,usage_scene),updated_at=? where id=?',(data.get('review_status'),data.get('score'),jdump(data['tags']) if 'tags' in data else None,data.get('remark'),data.get('usage_scene'),t,aid)); out=one(c,'select * from generated_assets where id=?',(aid,))
        else: out={'code':'not_found','message':'接口不存在','details':{}}; status=404
        c.commit(); c.close(); self.send(status,out)
def worker():
    while True:
        c=db(); jobs=rows(c,'select * from generation_jobs where job_status="pending"');
        for j in jobs:
            c.execute('update generation_jobs set job_status="running",started_at=? where id=?',(now(),j['id'])); c.execute('insert into generation_job_events(job_id,event_type,event_message,created_at) values(?,?,?,?)',(j['id'],'running','任务开始执行',now())); c.commit(); time.sleep(.15); asset_url='/demo-assets/'+str(j['id'])+'.'+('mp4' if j['job_kind']=='video' else 'png'); c.execute('update generation_jobs set job_status="succeeded",finished_at=?,result_json=? where id=?',(now(),jdump({'asset_url':asset_url}),j['id'])); c.execute('insert into generation_job_events(job_id,event_type,event_message,created_at) values(?,?,?,?)',(j['id'],'succeeded','演示素材已生成',now())); c.execute('insert or ignore into generated_assets(product_id,creative_plan_id,job_id,asset_type,asset_url,created_at,updated_at) values(?,?,?,?,?,?,?)',(j['product_id'],j['creative_plan_id'],j['id'],j['job_kind'],asset_url,now(),now())); c.commit()
        c.close(); time.sleep(1)
if __name__=='__main__':
    init(); threading.Thread(target=worker,daemon=True).start(); print('Ecommerce assistant: http://127.0.0.1:8000'); ThreadingHTTPServer(('127.0.0.1',8000),Handler).serve_forever()
