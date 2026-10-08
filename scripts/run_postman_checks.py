# Lightweight Postman-contract smoke test using the simulator.
import httpx
H={'Authorization':'Bearer demo-token'}; b='http://localhost:8000'
print(httpx.get(b+'/health').json())
a=httpx.get(b+'/assets/search',params={'query':'Boiler Feed Pump 101'},headers=H).json()['results'][0]['asset_id']; print('asset',a)
rows=httpx.get(b+'/alarms',params={'asset_id':a,'page':1,'page_size':50},headers=H).json()['data']; print('alarms',len(rows))
print(httpx.get(b+'/assets/'+a+'/metadata',headers=H).json()['asset_id'])
