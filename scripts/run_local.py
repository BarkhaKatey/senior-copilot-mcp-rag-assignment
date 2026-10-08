from __future__ import annotations
import subprocess,sys,time,os
procs=[]
commands=[
 [sys.executable,'-m','uvicorn','apps.backend.main:app','--host','0.0.0.0','--port','8000'],
 [sys.executable,'-m','uvicorn','mcp_servers.alarm_management.server:app','--host','0.0.0.0','--port','9000'],
 [sys.executable,'-m','uvicorn','apps.backend.copilot_api:app','--host','0.0.0.0','--port','9100'],
 [sys.executable,'apps/frontend/server.py']]
for c in commands: procs.append(subprocess.Popen(c))
print('ABB Copilot services started: GUI http://localhost:9200 | Copilot http://localhost:9100 | MCP http://localhost:9000 | API http://localhost:8000')
try:
 while True: time.sleep(1)
except KeyboardInterrupt:
 for p in procs: p.terminate()
