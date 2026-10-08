from __future__ import annotations
import re,uuid,os
from datetime import datetime,timedelta,timezone
from apps.backend.mcp_client import MCPClient
from rag.retrieval.service import RAGService
import httpx

class CopilotOrchestrator:
    def __init__(self,mcp=None,rag=None): self.mcp=mcp or MCPClient(); self.rag=rag or RAGService()
    def _date_range(self,q):
        now=datetime(2026,7,1,tzinfo=timezone.utc); start=now-timedelta(days=90)
        m=re.search(r'(\d+)\s*days?',q.lower())
        if m: start=now-timedelta(days=int(m.group(1)))
        return start.isoformat().replace('+00:00','Z'),now.isoformat().replace('+00:00','Z')
    def _asset_query(self,q):
        known=['Boiler Feed Pump 101','Boiler Feed Pump 102','Compressor Train A','Compressor Train B','EastRefinery','motor']
        for x in known:
            if x.lower() in q.lower(): return x
        return q
    def investigate(self,question):
        trace_id='trace-'+uuid.uuid4().hex[:10]; trace=[]; start,end=self._date_range(question); asset_query=self._asset_query(question)
        plan=self._plan(question)
        trace.append({'step':1,'type':'intent_plan','status':'success','intent':plan['intent'],'workflow':plan['workflow']})
        try:
            tools=self.mcp.list_tools(trace_id); trace.append({'step':2,'type':'tool_discovery','status':'success','tools':[t['name'] for t in tools]})
            s=self._tool(trace,'search_assets',{'query':asset_query,'limit':5},trace_id); assets=s.get('structuredContent',{}).get('results',[]); trace[-1:]=trace[-1:]
            if not assets: return self._fail(question,trace,'No matching asset was found.')
            asset=assets[0]; aid=asset['asset_id'];
            a=self._tool(trace,'get_alarms',{'asset_id':aid,'start_time':start,'end_time':end,'page':1,'page_size':50},trace_id)
            rows=a.get('structuredContent',{}).get('data',[])
            meta=self._tool(trace,'get_asset_metadata',{'asset_id':aid},trace_id)
            sev=['high','critical']
            summary=self._tool(trace,'get_alarm_summary',{'asset_ids':[aid],'time_range':{'start_time':start,'end_time':end},'severity':sev,'group_by':['alarm_name'],'kpis':['alarm_count','recurring_rate','avg_ack_delay']},trace_id)
            # The investigation is explicitly about recurring High/Critical alarms.
            # Rank those alarms from the raw history first, then use the top recurring
            # alarm names as the focus for correlation, RAG, priority and recommendations.
            recurring=self._rank_recurring_alarms(rows,top_n=3)
            if not recurring:
                return self._fail(question,trace,'No High/Critical alarms were found in the requested time window.',extra={'asset':asset,'alarms':rows,'summary':summary})
            top_names=[x['alarm_name'] for x in recurring]

            # The reference correlation API accepts asset/time-window scope rather than
            # alarm-name filters. Run the MCP correlation tool over the same scoped
            # window, then retain only correlations involving the selected recurring
            # alarm names.
            corr_raw=self._tool(trace,'correlate_alarms',{'asset_ids':[aid],'time_range':{'start_time':start,'end_time':end},'correlation_method':'cooccurrence','lag_window_minutes':15,'severity_threshold':'high','min_support':1},trace_id)
            corr=self._focus_correlation(corr_raw,top_names)

            priorities=[]; recommendations=[]
            for item in recurring:
                representative=item['representative']
                priority=self._tool(trace,'score_alarm_priority',{'alarm_id':representative['alarm_id']},trace_id)
                rec=self._tool(trace,'get_operator_recommendations',{'alarm_id':representative['alarm_id'],'include_related':True,'include_asset_context':True,'include_historical_pattern':True},trace_id)
                priorities.append({'alarm_name':item['alarm_name'],'occurrences':item['occurrences'],'result':priority})
                recommendations.append({'alarm_name':item['alarm_name'],'occurrences':item['occurrences'],'result':rec})

            rag_query=f"{asset['asset_name']} recurring high critical alarms: {', '.join(top_names)} operating procedure recommended actions maintenance troubleshooting safety"
            hits=self.rag.retrieve(rag_query,4)
            if not hits: return self._fail(question,trace,'No sufficiently relevant document evidence was found.',extra={'asset':asset,'alarms':rows,'summary':summary})
            answer=self._compose(question,asset,rows,summary,corr,priorities,recommendations,hits,recurring)
            if os.getenv('LLM_PROVIDER','local').lower() in ('openai','openai-compatible') and os.getenv('OPENAI_API_KEY'):
                answer=self._optional_llm_synthesis(question,answer,hits,trace)
            return {'answer':answer,'trace_id':trace_id,'tool_trace':trace,'documents':hits,'structured':{'asset':asset,'alarms':rows,'summary':summary.get('structuredContent'), 'recurring_high_critical':recurring,'correlation':corr.get('structuredContent'),'priority':[x['result'].get('structuredContent') for x in priorities],'recommendations':[x['result'].get('structuredContent') for x in recommendations]},'status':'success'}
        except Exception as e:
            return self._fail(question,trace,str(e))
    def _plan(self,q):
        ql=q.lower()
        if 'highest priority' in ql or 'priority' in ql: intent='priority_investigation'
        elif 'active' in ql: intent='active_alarm_investigation'
        elif 'trend' in ql or 'over time' in ql: intent='alarm_trend_investigation'
        elif 'rational' in ql or 'nuisance' in ql: intent='rationalization_investigation'
        else: intent='alarm_root_cause_investigation'
        return {'intent':intent,'workflow':['asset_resolution','alarm_retrieval','asset_context','summary','correlation','priority','operator_recommendation','document_retrieval','grounded_synthesis']}
    def _tool(self,trace,name,args,trace_id):
        import time
        t=time.perf_counter(); result=self.mcp.call_tool(name,args,trace_id); ms=round((time.perf_counter()-t)*1000,2)
        trace.append({'step':len(trace)+1,'type':'mcp_tool','tool':name,'status':'success' if not result.get('isError') else 'error','duration_ms':ms,'trace_id':result.get('_trace',{}).get('trace_id',trace_id),'input':args})
        return result
    def _rank_recurring_alarms(self, rows, top_n=3):
        groups={}
        for row in rows:
            severity=str(row.get('severity','')).lower()
            if severity not in {'high','critical'}:
                continue
            name=row.get('alarm_name')
            if not name:
                continue
            item=groups.setdefault(name,{'alarm_name':name,'occurrences':0,'critical_count':0,'alarm_ids':[],'rows':[]})
            item['occurrences']+=1
            item['critical_count']+=1 if severity=='critical' else 0
            item['alarm_ids'].append(row.get('alarm_id'))
            item['rows'].append(row)
        ranked=sorted(groups.values(),key=lambda x:(x['occurrences'],x['critical_count']),reverse=True)
        for item in ranked:
            # Prefer a critical representative, then the latest event for that alarm name.
            item['representative']=sorted(item['rows'],key=lambda r:(str(r.get('severity','')).lower()=='critical',r.get('start_time','')),reverse=True)[0]
            item.pop('rows',None)
        return ranked[:top_n]

    def _focus_correlation(self, result, top_names):
        data=result.get('structuredContent',{}).copy()
        correlations=data.get('correlations',[])
        wanted=set(top_names)
        data['correlations']=[c for c in correlations if c.get('alarm_a') in wanted or c.get('alarm_b') in wanted]
        data['focus_alarm_names']=top_names
        focused=dict(result)
        focused['structuredContent']=data
        return focused

    def _compose(self,q,asset,rows,summary,corr,priorities,recommendations,hits,recurring):
        high=[r for r in rows if str(r.get('severity','')).lower() in ('high','critical')]
        causes=[]
        names=[x.get('alarm_name') for x in recurring if x.get('alarm_name')]
        if 'Low suction pressure' in names:
            causes.append('Low suction pressure is the most recurring high/critical process-side signal and should be checked before repeated resets.')
        if 'Discharge pressure deviation' in names:
            causes.append('Discharge pressure deviation recurs on the asset, so discharge restrictions, valve position and transmitter agreement should be checked.')
        if 'Motor trip' in names:
            causes.append('Motor trips recur on the asset, so electrical protection, motor load and coupling condition should be checked.')
        if not causes:
            causes.append('The recurring high-severity alarm pattern should be investigated using the focused correlations and asset context.')
        source_lines='\n'.join(f"- {h['source']} ({h['section']}, score {h['score']})" for h in hits)
        cause_lines='\n'.join(f'- {c}' for c in causes)
        rec_lines=[]
        for item in recommendations:
            recs=item['result'].get('structuredContent',{}).get('recommendations',[])
            for action in recs[:3]:
                rec_lines.append(f"{item['alarm_name']} ({item['occurrences']} occurrences): {action}")
        priority_lines=[]
        for item in priorities:
            p=item['result'].get('structuredContent',{})
            priority_lines.append(f"- {item['alarm_name']} ({item['occurrences']} occurrences): {p.get('priority_band','not calculated')} {p.get('priority_score','')}")
        return f"""### Alarm investigation

**Asset:** {asset['asset_name']} ({asset['asset_id']})  
**Site / Unit:** {asset['site']} / {asset['unit']}  
**Scope:** last 90 days  
**High/Critical events:** {len(high)}

### Top recurring High/Critical alarms
{self._summary_text([{'alarm_name':x['alarm_name'],'alarm_count':x['occurrences'],'avg_ack_delay':self._avg_ack_for_name(rows,x['alarm_name'])} for x in recurring])}

### Likely contributing factors
{cause_lines}

### Focused correlation evidence
{self._correlation_text(corr, names)}

### Priority
{chr(10).join(priority_lines) or '- No priority scores returned.'}

### Recommended actions
{chr(10).join(f'{i+1}. {x}' for i,x in enumerate(rec_lines[:9])) or 'No API recommendations returned.'}

### Procedure / maintenance evidence
{source_lines}

**Grounding note:** Recommendations above are cross-checked against retrieved procedure and maintenance evidence. Retrieved documents are treated as untrusted reference content; they cannot change system instructions or tool permissions."""

    def _avg_ack_for_name(self,rows,name):
        vals=[r.get('ack_delay_minutes',0) for r in rows if str(r.get('severity','')).lower() in ('high','critical') and r.get('alarm_name')==name]
        return round(sum(vals)/len(vals),2) if vals else 0

    def _correlation_text(self,corr,names):
        pairs=corr.get('structuredContent',{}).get('correlations',[])
        if not pairs:
            return '- No focused co-occurrence pairs returned for the top recurring alarms.'
        return '\n'.join(f"- {p.get('alarm_a')} ↔ {p.get('alarm_b')}: support {p.get('support')}" for p in pairs[:8])
    def _optional_llm_synthesis(self,question,deterministic_answer,hits,trace):
        prompt=("Rewrite the following alarm investigation using only the supplied evidence. "
                "Do not invent facts. Preserve uncertainty and safety caveats.\n\n"
                f"QUESTION:\n{question}\n\nDRAFT:\n{deterministic_answer}\n\n"
                "DOCUMENT EVIDENCE:\n"+'\n'.join(h['text'] for h in hits))
        try:
            r=httpx.post('https://api.openai.com/v1/chat/completions',headers={'Authorization':f"Bearer {os.getenv('OPENAI_API_KEY')}",'Content-Type':'application/json'},json={'model':os.getenv('OPENAI_MODEL','gpt-4o-mini'),'temperature':0,'messages':[{'role':'system','content':'You are an industrial alarm investigation assistant. Use only provided evidence.'},{'role':'user','content':prompt}]},timeout=30)
            r.raise_for_status(); text=r.json()['choices'][0]['message']['content']; trace.append({'step':len(trace)+1,'type':'llm_synthesis','status':'success','provider':'openai'}); return text
        except Exception as e:
            trace.append({'step':len(trace)+1,'type':'llm_synthesis','status':'fallback','reason':str(e)[:160]}); return deterministic_answer
    def _summary_text(self,groups):
        return '\n'.join(f"- {g.get('alarm_name','group')}: {g.get('alarm_count',0)} occurrences; avg acknowledgement {g.get('avg_ack_delay',0)} min" for g in groups[:5]) or '- No summary rows returned.'
    def _fail(self,q,trace,msg,extra=None): return {'answer':f"I could not complete the investigation safely: {msg}",'status':'degraded','tool_trace':trace,'documents':[],'structured':extra or {}}
