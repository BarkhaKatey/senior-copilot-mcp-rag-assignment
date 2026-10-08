import os
from dotenv import load_dotenv
load_dotenv()

ALARM_API_BASE_URL=os.getenv('ALARM_API_BASE_URL','http://localhost:8000')
ALARM_API_TOKEN=os.getenv('ALARM_API_TOKEN','demo-token')
MCP_SERVER_URL=os.getenv('MCP_SERVER_URL','http://localhost:9000/mcp')
MCP_SERVER_TOKEN=os.getenv('MCP_SERVER_TOKEN','demo-token')
RAG_DOCUMENT_PATH=os.getenv('RAG_DOCUMENT_PATH','./rag/documents')
RAG_INDEX_PATH=os.getenv('RAG_INDEX_PATH','./rag/index')
LLM_PROVIDER=os.getenv('LLM_PROVIDER','local')
OPENAI_API_KEY=os.getenv('OPENAI_API_KEY','')
OPENAI_MODEL=os.getenv('OPENAI_MODEL','gpt-4o-mini')
REQUEST_TIMEOUT_SECONDS=float(os.getenv('REQUEST_TIMEOUT_SECONDS','10'))
MAX_RETRIES=int(os.getenv('MAX_RETRIES','2'))
LOG_LEVEL=os.getenv('LOG_LEVEL','INFO')
