from fastapi.testclient import TestClient
import mcp_servers.alarm_management.server as server
c=TestClient(server.app); H={'Authorization':'Bearer demo-token'}
def rpc(method,params=None):
    return c.post('/mcp',json={'jsonrpc':'2.0','id':'1','method':method,'params':params or {}},headers=H)
def test_tool_discovery():
    d=rpc('tools/list').json()['result']; names={x['name'] for x in d['tools']}; assert {'search_assets','get_alarms','get_alarm_summary','correlate_alarms'}<=names
def test_tool_call(monkeypatch):
    monkeypatch.setattr(server.client,'search_assets',lambda **kwargs:{'results':[{'asset_id':'AST-BFP-101','asset_name':'Boiler Feed Pump 101'}],'total':1})
    d=rpc('tools/call',{'name':'search_assets','arguments':{'query':'Boiler Feed Pump 101'}}).json()['result']; assert d['structuredContent']['results'][0]['asset_id']=='AST-BFP-101'
def test_auth_required(): assert c.post('/mcp',json={'jsonrpc':'2.0','id':'1','method':'tools/list'}).status_code==401
