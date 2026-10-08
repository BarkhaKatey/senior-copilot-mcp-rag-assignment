from fastapi import FastAPI
from pydantic import BaseModel
from apps.backend.orchestrator import CopilotOrchestrator
app=FastAPI(title='ABB Alarm Investigation Copilot',version='1.0.0')
class ChatRequest(BaseModel): message:str
orch=CopilotOrchestrator()
@app.get('/health')
def health(): return {'status':'ok','service':'copilot'}
@app.post('/chat')
def chat(req:ChatRequest): return orch.investigate(req.message)
