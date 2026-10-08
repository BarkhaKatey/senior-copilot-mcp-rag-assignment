install:
	python -m pip install -r requirements.txt

run-api:
	uvicorn apps.backend.main:app --host 0.0.0.0 --port 8000 --reload

run-mcp:
	uvicorn mcp_servers.alarm_management.server:app --host 0.0.0.0 --port 9000 --reload

run-copilot:
	uvicorn apps.backend.copilot_api:app --host 0.0.0.0 --port 9100 --reload

run-gui:
	python apps/frontend/server.py

rag-index:
	python -m rag.ingestion.build_index

test:
	pytest -q --cov=. --cov-report=term-missing

lint:
	ruff check .

all:
	python scripts/run_local.py
