import json, os, threading, time, unittest, urllib.request
from app import init, Handler, ThreadingHTTPServer, worker
class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists('ecommerce.db'): os.remove('ecommerce.db')
        init(); cls.server=ThreadingHTTPServer(('127.0.0.1',8765),Handler); threading.Thread(target=cls.server.serve_forever,daemon=True).start(); threading.Thread(target=worker,daemon=True).start()
    @classmethod
    def tearDownClass(cls): cls.server.shutdown()
    def req(self,path,body=None,token=None,method=None):
        method=method or ('POST' if body is not None else 'GET')
        r=urllib.request.Request('http://127.0.0.1:8765/api/v1'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+token} if token else {})},method=method); return json.loads(urllib.request.urlopen(r).read())
    def test_login_demo_and_diagnosis(self):
        d=self.req('/auth/login',{'username':'admin','password':'admin123'}); t=d['access_token']; demo=self.req('/workspace/demo-data',{},t); pid=demo['product_id']; p=self.req('/products/'+str(pid),token=t); self.assertEqual(p['name'],'轻量防晒伞'); diag=self.req('/products/'+str(pid)+'/diagnoses/generate',{},t); self.assertIn('positioning',diag)
        plan=self.req('/products/'+str(pid)+'/creative-plans/main-images/generate',{},t); job=self.req('/products/'+str(pid)+'/creative-plans/'+str(plan['id'])+'/images/generate',{},t); self.assertEqual(job['job_status'],'pending'); time.sleep(2); detail=self.req('/products/'+str(pid),token=t); self.assertEqual(detail['jobs'][0]['job_status'],'succeeded'); self.assertEqual(len(detail['assets']),1); asset=detail['assets'][0]; updated=self.req('/products/'+str(pid)+'/assets/'+str(asset['id']),{'review_status':'approved','score':4.5},t,method='PATCH'); self.assertEqual(updated['review_status'],'approved')
if __name__=='__main__': unittest.main()
