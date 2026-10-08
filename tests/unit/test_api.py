from fastapi.testclient import TestClient
from apps.backend.main import app
c=TestClient(app); H={'Authorization':'Bearer demo-token'}
def test_health(): assert c.get('/health').status_code==200
def test_asset_search():
 r=c.get('/assets/search',params={'query':'Boiler Feed Pump 101'},headers=H); assert r.status_code==200; assert r.json()['results'][0]['asset_id']=='AST-BFP-101'
def test_pagination_and_alarm():
 r=c.get('/alarms',params={'asset_id':'AST-BFP-101','page':1,'page_size':2},headers=H); assert r.status_code==200; assert len(r.json()['data'])<=2

def test_summary():
 p={'asset_ids':['AST-BFP-101'],'time_range':{'start_time':'2026-05-01T00:00:00Z','end_time':'2026-07-01T00:00:00Z'},'severity':['high','critical'],'group_by':['alarm_name'],'kpis':['alarm_count']}
 r=c.post('/alarms/summary',json=p,headers=H); assert r.status_code==200; assert r.json()['groups']
