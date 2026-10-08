import subprocess,time,sys,os
from apps.backend.orchestrator import CopilotOrchestrator
from apps.backend.mcp_client import MCPClient
from rag.ingestion.build_index import main

def test_rag_index_build(): main(); assert os.path.exists('rag/index/index.json')

def test_recurring_alarm_ranking_filters_and_sorts():
    orch=CopilotOrchestrator(mcp=object(), rag=object())
    rows=[
        {'alarm_id':'a1','alarm_name':'Motor trip','severity':'high','start_time':'2026-06-01T00:00:00Z'},
        {'alarm_id':'a2','alarm_name':'Low suction pressure','severity':'critical','start_time':'2026-06-02T00:00:00Z'},
        {'alarm_id':'a3','alarm_name':'Low suction pressure','severity':'high','start_time':'2026-06-03T00:00:00Z'},
        {'alarm_id':'a4','alarm_name':'Low suction pressure','severity':'high','start_time':'2026-06-04T00:00:00Z'},
        {'alarm_id':'a5','alarm_name':'Discharge pressure deviation','severity':'high','start_time':'2026-06-05T00:00:00Z'},
        {'alarm_id':'a6','alarm_name':'Discharge pressure deviation','severity':'critical','start_time':'2026-06-06T00:00:00Z'},
        {'alarm_id':'a7','alarm_name':'Low suction pressure','severity':'low','start_time':'2026-06-07T00:00:00Z'},
    ]
    ranked=orch._rank_recurring_alarms(rows,top_n=3)
    assert [(x['alarm_name'],x['occurrences']) for x in ranked] == [
        ('Low suction pressure',3),
        ('Discharge pressure deviation',2),
        ('Motor trip',1),
    ]
    assert ranked[0]['representative']['alarm_id']=='a2'
    assert all(r['severity'] in {'high','critical'} for item in ranked for r in [item['representative']])
