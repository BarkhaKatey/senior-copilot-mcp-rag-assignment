from __future__ import annotations
import json,os,urllib.request
from http.server import BaseHTTPRequestHandler,HTTPServer
BACKEND=os.getenv('COPILOT_BACKEND_URL','http://localhost:9100')
HTML='''<!doctype html><html><head><meta charset="utf-8"><title>ABB Alarm Investigation Copilot</title><style>body{font-family:Inter,Arial;margin:0;background:#f5f7fa;color:#18212f}.wrap{max-width:1180px;margin:0 auto;padding:24px}.card{background:white;border:1px solid #dfe5ec;border-radius:12px;padding:18px;margin:14px 0;box-shadow:0 2px 8px #0000000a}textarea{width:100%;min-height:90px;border:1px solid #c9d2df;border-radius:8px;padding:10px;font-size:15px;box-sizing:border-box}button{background:#1f6feb;color:white;border:0;border-radius:8px;padding:11px 18px;margin-top:10px;cursor:pointer}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.pill{display:inline-block;padding:4px 8px;border-radius:12px;background:#eef3f8;margin:2px;font-size:12px}pre{white-space:pre-wrap;word-break:break-word;background:#f7f9fb;padding:12px;border-radius:8px}.muted{color:#667085}details{margin-top:10px}@media(max-width:800px){.grid{grid-template-columns:1fr}}</style></head><body><div class="wrap"><h1>ABB Alarm Investigation Copilot</h1><p class="muted">MCP + RAG evidence-backed alarm investigation</p><div class="card"><textarea id="q">Investigate recurring high-severity alarms for Boiler Feed Pump 101 over the last 90 days, identify likely contributing factors, retrieve the relevant operating procedure, and recommend actions.</textarea><br><button onclick="run()">Investigate</button></div><div id="out"></div></div><script>async function run(){const q=document.getElementById('q').value;document.getElementById('out').innerHTML='<div class="card">Running MCP tools and RAG retrieval…</div>';try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:q})});const d=await r.json();let docs=(d.documents||[]).map(x=>`<li><b>${x.source}</b> — ${x.section} <span class="pill">score ${x.score}</span></li>`).join('');let trace=(d.tool_trace||[]).map(x=>`<li>${x.type} ${x.tool||''} — <b>${x.status}</b> ${x.duration_ms?x.duration_ms+' ms':''}</li>`).join('');document.getElementById('out').innerHTML=`<div class="grid"><div class="card"><h2>Investigation</h2><pre>${escape(d.answer||'')}</pre></div><div class="card"><h2>Document evidence</h2><ul>${docs||'<li>No documents</li>'}</ul></div></div><div class="card"><details><summary><b>MCP execution trace</b></summary><ol>${trace}</ol><p class="muted">Trace ID: ${escape(d.trace_id||'n/a')}</p></details></div>`}catch(e){document.getElementById('out').innerHTML='<div class="card">Error: '+escape(e.message)+'</div>'}}function escape(s){return String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}</script></body></html>'''
class H(BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path=='/': self.send(200,'text/html',HTML.encode())
  else: self.send(404,'text/plain',b'not found')
 def do_POST(self):
  if self.path!='/api/chat': return self.send(404,'text/plain',b'not found')
  n=int(self.headers.get('Content-Length','0')); body=self.rfile.read(n)
  req=urllib.request.Request(BACKEND+'/chat',data=body,headers={'Content-Type':'application/json'},method='POST')
  try:
   with urllib.request.urlopen(req,timeout=120) as r: data=r.read(); self.send(200,'application/json',data)
  except Exception as e: self.send(502,'application/json',json.dumps({'error':str(e)}).encode())
 def send(self,status,ctype,data):
  self.send_response(status); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
if __name__=='__main__': HTTPServer(('0.0.0.0',9200),H).serve_forever()
