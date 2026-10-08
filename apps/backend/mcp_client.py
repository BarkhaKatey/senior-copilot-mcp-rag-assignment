from __future__ import annotations
import json,uuid,httpx
from apps.backend.config import MCP_SERVER_URL,MCP_SERVER_TOKEN,REQUEST_TIMEOUT_SECONDS
class MCPClientError(RuntimeError): pass
class MCPClient:
    def __init__(self,url=MCP_SERVER_URL,token=MCP_SERVER_TOKEN): self.url=url; self.token=token
    def _call(self,method,params=None,trace_id=None):
        body={'jsonrpc':'2.0','id':str(uuid.uuid4()),'method':method,'params':params or {}}
        headers={'Authorization':f'Bearer {self.token}','trace_id':trace_id or str(uuid.uuid4())}
        r=httpx.post(self.url,json=body,headers=headers,timeout=REQUEST_TIMEOUT_SECONDS)
        r.raise_for_status(); data=r.json()
        if 'error' in data: raise MCPClientError(data['error'].get('message','MCP error'))
        return data['result']
    def initialize(self,trace_id=None): return self._call('initialize',{},trace_id)
    def list_tools(self,trace_id=None): return self._call('tools/list',{},trace_id).get('tools',[])
    def call_tool(self,name,arguments,trace_id=None): return self._call('tools/call',{'name':name,'arguments':arguments},trace_id)
