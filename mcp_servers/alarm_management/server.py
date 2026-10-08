from __future__ import annotations
import sys, os, uuid, time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from connectors.alarm_api.client import AlarmAPIClient, AlarmAPIError
from apps.backend.config import MCP_SERVER_TOKEN

app=FastAPI(title='ABB Alarm Management MCP Server',version='1.0.0')
client=AlarmAPIClient()
TOOLS=[
 {'name':'search_assets','description':'Resolve plant asset names or types to asset IDs.','inputSchema':{'type':'object','properties':{'query':{'type':'string'},'limit':{'type':'integer','default':10},'unit':{'type':'string'},'site':{'type':'string'}},'required':['query']}},
 {'name':'get_asset_metadata','description':'Retrieve asset metadata and related assets.','inputSchema':{'type':'object','properties':{'asset_id':{'type':'string'}},'required':['asset_id']}},
 {'name':'get_alarms','description':'Retrieve active or historical alarms with pagination and filters.','inputSchema':{'type':'object','properties':{'asset_id':{'type':'string'},'unit':{'type':'string'},'site':{'type':'string'},'status':{'type':'string'},'start_time':{'type':'string'},'end_time':{'type':'string'},'page':{'type':'integer','default':1},'page_size':{'type':'integer','default':50}},'required':[]}},
 {'name':'get_alarm_summary','description':'Aggregate alarms by alarm name, asset, severity or other dimensions.','inputSchema':{'type':'object','properties':{'asset_ids':{'type':'array','items':{'type':'string'}},'site':{'type':'string'},'unit':{'type':'string'},'time_range':{'type':'object'},'severity':{'type':'array'},'group_by':{'type':'array'},'kpis':{'type':'array'}},'required':[]}},
 {'name':'get_alarm_trends','description':'Return alarm counts and acknowledgement-delay trends.','inputSchema':{'type':'object','properties':{'asset_ids':{'type':'array'},'site':{'type':'string'},'unit':{'type':'string'},'time_range':{'type':'object'},'bucket':{'type':'string'},'metrics':{'type':'array'}},'required':[]}},
 {'name':'correlate_alarms','description':'Find co-occurring alarms across selected assets and a time window.','inputSchema':{'type':'object','properties':{'asset_ids':{'type':'array'},'time_range':{'type':'object'},'correlation_method':{'type':'string'},'lag_window_minutes':{'type':'integer'},'severity_threshold':{'type':'string'},'min_support':{'type':'integer'}},'required':['asset_ids']}},
 {'name':'score_alarm_priority','description':'Calculate priority score and contributing factors for an alarm.','inputSchema':{'type':'object','properties':{'alarm_id':{'type':'string'}},'required':['alarm_id']}},
 {'name':'get_operator_recommendations','description':'Retrieve operator actions, related assets and historical pattern.','inputSchema':{'type':'object','properties':{'alarm_id':{'type':'string'},'include_related':{'type':'boolean'},'include_asset_context':{'type':'boolean'},'include_historical_pattern':{'type':'boolean'}},'required':['alarm_id']}},
 {'name':'get_rationalization_candidates','description':'Identify frequently recurring alarms that may warrant rationalization.','inputSchema':{'type':'object','properties':{'asset_ids':{'type':'array'},'site':{'type':'string'},'unit':{'type':'string'},'time_range':{'type':'object'},'recurrence_threshold':{'type':'integer'},'stale_minutes_threshold':{'type':'integer'}},'required':[]}},
]

def auth(request):
    if request.headers.get('authorization') != f'Bearer {MCP_SERVER_TOKEN}': raise HTTPException(401,'Invalid MCP authorization')

def call_tool(name,args,trace_id):
    if name=='search_assets': return client.search_assets(trace_id=trace_id,**args)
    if name=='get_asset_metadata': return client.asset_metadata(trace_id=trace_id,**args)
    if name=='get_alarms': return client.alarms(_trace_id=trace_id,**args)
    if name=='get_alarm_summary': return client.summary(args,trace_id=trace_id)
    if name=='get_alarm_trends': return client.trends(args,trace_id=trace_id)
    if name=='correlate_alarms': return client.correlation(args,trace_id=trace_id)
    if name=='score_alarm_priority': return client.priority(args,trace_id=trace_id)
    if name=='get_operator_recommendations': return client.recommendations(args,trace_id=trace_id)
    if name=='get_rationalization_candidates': return client.rationalization(args,trace_id=trace_id)
    raise KeyError(name)

@app.get('/health')
def health(): return {'status':'ok','service':'alarm-mcp','tools':len(TOOLS)}

@app.post('/mcp')
async def mcp_endpoint(request:Request):
    auth(request); body=await request.json(); method=body.get('method'); rid=body.get('id'); trace_id=request.headers.get('trace_id') or str(uuid.uuid4())
    try:
        if method=='initialize':
            result={'protocolVersion':'2025-06-18','capabilities':{'tools':{}},'serverInfo':{'name':'abb-alarm-management','version':'1.0.0'}}
        elif method in ('notifications/initialized','ping'):
            result={}
        elif method=='tools/list': result={'tools':TOOLS}
        elif method=='tools/call':
            params=body.get('params',{}); name=params.get('name'); args=params.get('arguments') or {}
            if not name: raise ValueError('Tool name is required')
            started=time.perf_counter()
            data=call_tool(name,args,trace_id)
            elapsed=round((time.perf_counter()-started)*1000,2)
            result={'content':[{'type':'text','text':__import__('json').dumps(data)}],'structuredContent':data,'isError':False,'_trace':{'trace_id':trace_id,'tool':name,'duration_ms':elapsed}}
        else: raise ValueError(f'Unsupported MCP method: {method}')
        return {'jsonrpc':'2.0','id':rid,'result':result}
    except (AlarmAPIError,KeyError,ValueError,ValidationError,TypeError) as e:
        return JSONResponse(status_code=200,content={'jsonrpc':'2.0','id':rid,'error':{'code':-32000,'message':str(e)}})
