from __future__ import annotations
import json, math, os, uuid
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter, defaultdict
from typing import Any
from fastapi import FastAPI, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field
from apps.backend.config import ALARM_API_TOKEN

ROOT=Path(__file__).resolve().parents[2]
assets=json.loads((ROOT/'test-data/assets.json').read_text())
alarms=json.loads((ROOT/'test-data/alarms.json').read_text())
asset_map={a['asset_id']:a for a in assets}
alarm_map={a['alarm_id']:a for a in alarms}
calculations={}
app=FastAPI(title='ABB Alarm Management API Simulator',version='1.0.0')

class TimeRange(BaseModel):
    start_time:str
    end_time:str
class SummaryRequest(BaseModel):
    asset_ids:list[str]|None=None; site:str|None=None; unit:str|None=None; time_range:TimeRange|None=None
    severity:list[str]|None=None; alarm_types:list[str]|None=None; group_by:list[str]=[]; kpis:list[str]=[]
class TrendsRequest(BaseModel):
    asset_ids:list[str]|None=None; site:str|None=None; unit:str|None=None; time_range:TimeRange|None=None
    bucket:str='daily'; metrics:list[str]=[]
class CorrelationRequest(BaseModel):
    asset_ids:list[str]; time_range:TimeRange|None=None; correlation_method:str='cooccurrence'; lag_window_minutes:int=15; severity_threshold:str='medium'; min_support:int=1
class FloodRequest(BaseModel):
    unit:str; time_range:TimeRange; threshold_count:int=10; rolling_window_minutes:int=10
class RationalizationRequest(BaseModel):
    asset_ids:list[str]|None=None; site:str|None=None; unit:str|None=None; time_range:TimeRange|None=None; recurrence_threshold:int=5; stale_minutes_threshold:int=180
class PriorityRequest(BaseModel): alarm_id:str
class RecommendationRequest(BaseModel): alarm_id:str; include_related:bool=True; include_asset_context:bool=True; include_historical_pattern:bool=True
class CalculationRequest(BaseModel): calculation_type:str; filters:dict[str,Any]={}
class ExecuteCalculationRequest(BaseModel): calculation_id:str; filters:dict[str,Any]={}

def auth(authorization:str|None):
    if authorization != f'Bearer {ALARM_API_TOKEN}': raise HTTPException(401,'Invalid or missing bearer token')

def filtered_alarms(asset_ids=None,site=None,unit=None,status=None,start_time=None,end_time=None,severity=None,alarm_types=None):
    out=[]
    for a in alarms:
        asset=asset_map[a['asset_id']]
        if asset_ids and a['asset_id'] not in asset_ids: continue
        if site and asset['site']!=site: continue
        if unit and asset['unit']!=unit: continue
        if status and a['status']!=status: continue
        if severity and a['severity'] not in severity: continue
        if alarm_types and a['alarm_type'] not in alarm_types: continue
        if start_time and a['start_time']<start_time: continue
        if end_time and a['start_time']>end_time: continue
        out.append(a)
    return out

def trace(request:Request):
    return {'trace_id':request.headers.get('trace_id') or str(uuid.uuid4()),'client_id':request.headers.get('x-client-id'),'metadata_tag':request.headers.get('x-metadata-tag')}

@app.get('/health')
def health(): return {'status':'ok','service':'alarm-api-simulator','version':'1.0.0'}

@app.get('/assets/search')
def search_assets(request:Request,query:str,limit:int=10,unit:str|None=None,site:str|None=None,authorization:str|None=Header(None)):
    auth(authorization); q=query.lower(); rows=[]
    for a in assets:
        if q in a['asset_name'].lower() or q in a['asset_type'].lower() or q in a['asset_id'].lower():
            if unit and a['unit']!=unit: continue
            if site and a['site']!=site: continue
            rows.append(a)
    return {'results':rows[:max(1,min(limit,100))],'total':len(rows)}

@app.get('/assets/{asset_id}/metadata')
def metadata(asset_id:str,authorization:str|None=Header(None)):
    auth(authorization)
    if asset_id not in asset_map: raise HTTPException(404,'Asset not found')
    a=asset_map[asset_id]
    return {'asset_id':asset_id,'metadata':a,'related_assets':[asset_map[x] for x in a['related_assets'] if x in asset_map]}

@app.get('/alarms')
def get_alarms(request:Request,asset_id:str|None=None,unit:str|None=None,site:str|None=None,status:str|None=None,start_time:str|None=None,end_time:str|None=None,page:int=1,page_size:int=50,sort_by:str='start_time',sort_order:str='desc',authorization:str|None=Header(None)):
    auth(authorization)
    rows=filtered_alarms([asset_id] if asset_id else None,site,unit,status,start_time,end_time)
    if sort_by in {'start_time','severity','alarm_name'}: rows.sort(key=lambda x:x[sort_by],reverse=sort_order.lower()=='desc')
    page=max(1,page); page_size=max(1,min(page_size,200)); total=len(rows); start=(page-1)*page_size
    return {'data':rows[start:start+page_size],'pagination':{'page':page,'page_size':page_size,'total':total,'total_pages':math.ceil(total/page_size) if total else 0},'trace':trace(request)}

@app.get('/alarms/{alarm_id}')
def get_alarm(alarm_id:str,request:Request,authorization:str|None=Header(None)):
    auth(authorization)
    if alarm_id not in alarm_map: raise HTTPException(404,'Alarm not found')
    return {'alarm':alarm_map[alarm_id],'asset':asset_map[alarm_map[alarm_id]['asset_id']],'trace':trace(request)}

def summary_rows(rows,group_by):
    groups=defaultdict(list)
    for a in rows:
        asset=asset_map[a['asset_id']]
        vals={'asset_id':a['asset_id'],'asset_name':asset['asset_name'],'severity':a['severity'],'alarm_name':a['alarm_name'],'site':asset['site'],'unit':asset['unit']}
        key=tuple(vals.get(k) for k in group_by) if group_by else ('all',)
        groups[key].append(a)
    out=[]
    for key,rs in groups.items():
        item={k:v for k,v in zip(group_by,key)} if group_by else {'group':'all'}
        item.update({'alarm_count':len(rs),'recurring_rate':round(sum(1 for x in rs if rs.count(x)>1)/max(1,len(rs)),3),'avg_ack_delay':round(sum(x['ack_delay_minutes'] for x in rs)/len(rs),2)})
        item['critical_count']=sum(x['severity']=='critical' for x in rs)
        item['high_count']=sum(x['severity']=='high' for x in rs)
        out.append(item)
    return out

@app.post('/alarms/summary')
def alarm_summary(req:SummaryRequest,request:Request,authorization:str|None=Header(None)):
    auth(authorization); tr=req.time_range
    rows=filtered_alarms(req.asset_ids,req.site,req.unit,None,tr.start_time if tr else None,tr.end_time if tr else None,req.severity,req.alarm_types)
    return {'groups':summary_rows(rows,req.group_by),'total_alarms':len(rows),'kpis':req.kpis,'trace':trace(request)}

@app.post('/alarms/trends')
def alarm_trends(req:TrendsRequest,request:Request,authorization:str|None=Header(None)):
    auth(authorization); tr=req.time_range
    rows=filtered_alarms(req.asset_ids,req.site,req.unit,None,tr.start_time if tr else None,tr.end_time if tr else None)
    buckets=defaultdict(list)
    for a in rows: buckets[a['start_time'][:10]].append(a)
    points=[{'bucket':k,'alarm_count':len(v),'avg_ack_delay':round(sum(x['ack_delay_minutes'] for x in v)/len(v),2)} for k,v in sorted(buckets.items())]
    return {'bucket':req.bucket,'metrics':req.metrics,'points':points,'trace':trace(request)}

@app.post('/alarms/correlation')
def correlation(req:CorrelationRequest,request:Request,authorization:str|None=Header(None)):
    auth(authorization); tr=req.time_range; rows=filtered_alarms(req.asset_ids,None,None,None,tr.start_time if tr else None,tr.end_time if tr else None)
    by_name=Counter(x['alarm_name'] for x in rows if x['severity'] in {'critical','high','medium'})
    correlations=[]
    names=[n for n,c in by_name.items() if c>=req.min_support]
    for i,a in enumerate(names):
        for b in names[i+1:]: correlations.append({'alarm_a':a,'alarm_b':b,'support':min(by_name[a],by_name[b]),'method':req.correlation_method,'lag_window_minutes':req.lag_window_minutes})
    return {'asset_ids':req.asset_ids,'correlations':correlations[:20],'trace':trace(request)}

@app.post('/alarms/flood-analysis')
def flood(req:FloodRequest,request:Request,authorization:str|None=Header(None)):
    auth(authorization); rows=filtered_alarms(None,None,req.unit,None,req.time_range.start_time,req.time_range.end_time)
    by_day=defaultdict(list)
    for a in rows: by_day[a['start_time'][:10]].append(a)
    windows=[{'start':d+'T00:00:00Z','end':d+'T23:59:59Z','alarm_count':len(v)} for d,v in sorted(by_day.items()) if len(v)>=req.threshold_count]
    return {'unit':req.unit,'threshold_count':req.threshold_count,'rolling_window_minutes':req.rolling_window_minutes,'flood_windows':windows,'trace':trace(request)}

@app.post('/alarms/rationalization-candidates')
def rationalization(req:RationalizationRequest,request:Request,authorization:str|None=Header(None)):
    auth(authorization); tr=req.time_range; rows=filtered_alarms(req.asset_ids,req.site,req.unit,None,tr.start_time if tr else None,tr.end_time if tr else None)
    counts=Counter((x['asset_id'],x['alarm_name']) for x in rows)
    candidates=[]
    for (aid,name),count in counts.items():
        if count>=req.recurrence_threshold:
            candidates.append({'asset_id':aid,'asset_name':asset_map[aid]['asset_name'],'alarm_name':name,'occurrences':count,'reason':'high recurrence','stale_candidate':count>=req.recurrence_threshold})
    return {'candidates':sorted(candidates,key=lambda x:x['occurrences'],reverse=True),'trace':trace(request)}

@app.post('/alarms/priority-score')
def priority(req:PriorityRequest,request:Request,authorization:str|None=Header(None)):
    auth(authorization)
    if req.alarm_id not in alarm_map: raise HTTPException(404,'Alarm not found')
    a=alarm_map[req.alarm_id]; score={'critical':90,'high':75,'medium':50,'low':25}[a['severity']]
    recurrence=sum(1 for x in alarms if x['asset_id']==a['asset_id'] and x['alarm_name']==a['alarm_name'])
    score=min(100,score+min(10,recurrence))
    return {'alarm_id':req.alarm_id,'priority_score':score,'priority_band':'critical' if score>=90 else 'high' if score>=70 else 'medium' if score>=40 else 'low','factors':{'severity':a['severity'],'recurrence_count':recurrence},'trace':trace(request)}

@app.post('/recommendations/operator-actions')
def recommendations(req:RecommendationRequest,request:Request,authorization:str|None=Header(None)):
    auth(authorization)
    if req.alarm_id not in alarm_map: raise HTTPException(404,'Alarm not found')
    a=alarm_map[req.alarm_id]; asset=asset_map[a['asset_id']]
    action_map={
      'Low suction pressure':['Verify suction pressure and upstream feed conditions.','Inspect suction strainer and inlet valve position.','Do not restart until minimum suction pressure is confirmed.'],
      'Motor trip':['Verify motor protection relay status and electrical supply.','Inspect motor load and coupling condition before reset.','Follow the approved restart procedure before returning to service.'],
      'Discharge pressure deviation':['Check discharge valve position and downstream restriction.','Compare pressure transmitter reading with local gauge.'],
      'High bearing temperature':['Check lubrication and bearing condition.','Inspect cooling flow and temperature sensor health.'],
      'High discharge pressure':['Verify downstream valve position and pressure transmitter.','Check for process restriction before reducing load.'],
      'High vibration':['Inspect coupling, alignment and bearing condition.','Check vibration trend before continued operation.'],
      'Oil temperature high':['Verify lubrication flow and cooler performance.','Inspect oil level and temperature sensor.'],
      'Overcurrent':['Verify motor load and electrical supply.','Inspect protection relay and mechanical load.']}
    return {'alarm_id':req.alarm_id,'asset_id':a['asset_id'],'alarm_name':a['alarm_name'],'severity':a['severity'],'recommendations':action_map.get(a['alarm_name'],['Follow the applicable operating procedure and isolate the cause before reset.']),'related_assets':asset['related_assets'] if req.include_related else [],'historical_pattern':{'occurrences':sum(1 for x in alarms if x['asset_id']==a['asset_id'] and x['alarm_name']==a['alarm_name'])} if req.include_historical_pattern else None,'trace':trace(request)}

@app.post('/calculation-code/generate')
def calc_generate(req:CalculationRequest,request:Request,authorization:str|None=Header(None)):
    auth(authorization); cid='CAL-'+uuid.uuid4().hex[:10]; calculations[cid]={'type':req.calculation_type,'filters':req.filters}; return {'calculation_id':cid,'calculation_type':req.calculation_type,'status':'generated'}

@app.post('/calculation-code/execute')
def calc_execute(req:ExecuteCalculationRequest,request:Request,authorization:str|None=Header(None)):
    auth(authorization)
    if req.calculation_id not in calculations: raise HTTPException(404,'Calculation not found')
    c=calculations[req.calculation_id]; f=req.filters or c['filters']; unit=f.get('unit'); site=f.get('site'); rows=filtered_alarms(None,site,unit,None,f.get('start_time'),f.get('end_time'))
    return {'calculation_id':req.calculation_id,'calculation_type':c['type'],'result':{'alarm_count':len(rows),'critical_count':sum(x['severity']=='critical' for x in rows),'high_count':sum(x['severity']=='high' for x in rows),'index':round(min(100,len(rows)*3.1),2)}}

@app.get('/analytics/kpi-definitions')
def kpis(authorization:str|None=Header(None)):
    auth(authorization); return {'kpis':[{'name':'alarm_count','description':'Number of alarms in scope'},{'name':'recurring_rate','description':'Share of repeated alarm occurrences'},{'name':'avg_ack_delay','description':'Average acknowledgement delay in minutes'},{'name':'critical_count','description':'Number of critical alarms'}]}
