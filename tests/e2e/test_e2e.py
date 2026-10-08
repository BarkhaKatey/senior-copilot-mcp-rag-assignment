import os, subprocess, sys, time
import httpx

def test_e2e_mcp_and_rag():
    env=os.environ.copy(); env['PYTHONPATH']='.'
    procs=[]
    try:
        procs.append(subprocess.Popen([sys.executable,'-m','uvicorn','apps.backend.main:app','--host','127.0.0.1','--port','18000'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
        procs.append(subprocess.Popen([sys.executable,'-m','uvicorn','mcp_servers.alarm_management.server:app','--host','127.0.0.1','--port','19000'],env={**env,'ALARM_API_BASE_URL':'http://127.0.0.1:18000','MCP_SERVER_TOKEN':'demo-token'},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
        for _ in range(50):
            try:
                if httpx.get('http://127.0.0.1:18000/health').status_code==200 and httpx.get('http://127.0.0.1:19000/health').status_code==200: break
            except Exception: time.sleep(.1)
        headers={'Authorization':'Bearer demo-token'}
        tools=httpx.post('http://127.0.0.1:19000/mcp',json={'jsonrpc':'2.0','id':'1','method':'tools/list','params':{}},headers=headers).json()['result']['tools']
        assert any(t['name']=='search_assets' for t in tools)
        call=httpx.post('http://127.0.0.1:19000/mcp',json={'jsonrpc':'2.0','id':'2','method':'tools/call','params':{'name':'search_assets','arguments':{'query':'Boiler Feed Pump 101'}}},headers=headers).json()['result']
        assert call['structuredContent']['results'][0]['asset_id']=='AST-BFP-101'
        from rag.ingestion.build_index import main
        from rag.retrieval.service import RAGService
        main(); hits=RAGService('rag/index/index.json').retrieve('Boiler Feed Pump 101 operating procedure low suction pressure',3)
        assert hits and any('procedure' in h['source'] for h in hits)
    finally:
        for p in procs: p.terminate(); p.wait(timeout=5)
