from __future__ import annotations
import time, uuid
import httpx
from apps.backend.config import ALARM_API_BASE_URL, ALARM_API_TOKEN, REQUEST_TIMEOUT_SECONDS, MAX_RETRIES

class AlarmAPIError(RuntimeError): pass

class AlarmAPIClient:
    def __init__(self, base_url=ALARM_API_BASE_URL, token=ALARM_API_TOKEN, timeout=REQUEST_TIMEOUT_SECONDS, max_retries=MAX_RETRIES):
        self.base_url=base_url.rstrip('/'); self.token=token; self.timeout=timeout; self.max_retries=max_retries
    def _request(self, method, path, *, params=None, json=None, trace_id=None, client_id='copilot-mcp', metadata_tag='copilot'):
        headers={'Authorization':f'Bearer {self.token}','trace_id':trace_id or str(uuid.uuid4()),'x-client-id':client_id,'x-metadata-tag':metadata_tag}
        last=None
        for attempt in range(self.max_retries+1):
            try:
                r=httpx.request(method,self.base_url+path,params=params,json=json,headers=headers,timeout=self.timeout)
                if r.status_code >= 500 and attempt < self.max_retries:
                    time.sleep(0.1*(attempt+1)); continue
                if r.status_code >= 400: raise AlarmAPIError(f'Alarm API {r.status_code}: {r.text[:500]}')
                return r.json()
            except (httpx.TimeoutException,httpx.NetworkError) as e:
                last=e
                if attempt < self.max_retries: time.sleep(0.1*(attempt+1)); continue
        raise AlarmAPIError(f'Alarm API unavailable after retries: {last}')
    def search_assets(self,query,limit=10,unit=None,site=None,trace_id=None): return self._request('GET','/assets/search',params={'query':query,'limit':limit,'unit':unit,'site':site},trace_id=trace_id)
    def asset_metadata(self,asset_id,trace_id=None): return self._request('GET',f'/assets/{asset_id}/metadata',trace_id=trace_id)
    def alarms(self,**params): return self._request('GET','/alarms',params=params,trace_id=params.pop('_trace_id',None))
    def alarm(self,alarm_id,trace_id=None): return self._request('GET',f'/alarms/{alarm_id}',trace_id=trace_id)
    def summary(self,payload,trace_id=None): return self._request('POST','/alarms/summary',json=payload,trace_id=trace_id)
    def trends(self,payload,trace_id=None): return self._request('POST','/alarms/trends',json=payload,trace_id=trace_id)
    def correlation(self,payload,trace_id=None): return self._request('POST','/alarms/correlation',json=payload,trace_id=trace_id)
    def flood(self,payload,trace_id=None): return self._request('POST','/alarms/flood-analysis',json=payload,trace_id=trace_id)
    def rationalization(self,payload,trace_id=None): return self._request('POST','/alarms/rationalization-candidates',json=payload,trace_id=trace_id)
    def priority(self,payload,trace_id=None): return self._request('POST','/alarms/priority-score',json=payload,trace_id=trace_id)
    def recommendations(self,payload,trace_id=None): return self._request('POST','/recommendations/operator-actions',json=payload,trace_id=trace_id)
