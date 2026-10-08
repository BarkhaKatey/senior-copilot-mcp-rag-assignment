import json,httpx
q='Investigate recurring high-severity alarms for Boiler Feed Pump 101 over the last 90 days, identify likely contributing factors, retrieve the relevant operating procedure, and recommend actions.'
r=httpx.post('http://localhost:9100/chat',json={'message':q},timeout=120); r.raise_for_status(); d=r.json(); print(d['answer']); print('\nDOCUMENTS:'); print(json.dumps(d['documents'],indent=2)); print('\nTRACE:'); print(json.dumps(d['tool_trace'],indent=2))
