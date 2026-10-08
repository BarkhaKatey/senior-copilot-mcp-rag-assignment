# ABB Senior Software Engineer — Alarm Investigation & Procedure Guidance Copilot

A self-contained demonstration of an enterprise copilot integrating an Alarm Management API through MCP and combining structured alarm evidence with document RAG.

## What is included
- Candidate-developed Alarm Management API simulator based on ABB's supplied Postman collections
- MCP-compatible server with tool discovery and schema-aware tool invocation
- MCP client and multi-step copilot orchestration
- Local document ingestion + retrieval with citations
- Responsive browser GUI
- Unit, contract, RAG and orchestration tests
- Docker Compose packaging
- Architecture/API/RAG/tool documentation
- Original Postman collections under `postman/`

## Demo Video

A short end-to-end demonstration of the ABB Alarm Investigation and Procedure Guidance Copilot.

The demo covers:
- MCP tool discovery and execution
- Multi-step MCP tool chaining
- Alarm investigation and recurrence analysis
- RAG-based procedure retrieval
- Document citations and grounded recommendations
- Successful investigation scenario
- Failure/degraded scenario

**Demo video:**

[Watch the ABB Alarm Copilot Demo](https://drive.google.com/file/d/1NJuwFwFiBDYVLrMIx2WEZ_BIH61qLFL6/view?usp=sharing)

## Primary acceptance scenario
> Investigate recurring high-severity alarms for Boiler Feed Pump 101 over the last 90 days, identify likely contributing factors, retrieve the relevant operating procedure, and provide recommended actions with source evidence.

## Quick start in VS Code

### 1. Open the folder
Open this repository folder in VS Code.

### 2. Create a virtual environment
```bash
python3.12 -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create local configuration
```bash
cp .env.example .env
```
On Windows, copy the file manually if `cp` is unavailable.

### 5. Build the RAG index
```bash
python -m rag.ingestion.build_index
```

### 6. Start everything
```bash
python scripts/run_local.py
```

Open **http://localhost:9200**.

Services:
- GUI: http://localhost:9200
- Copilot API: http://localhost:9100
- MCP server: http://localhost:9000
- Alarm API simulator: http://localhost:8000

### Docker option
```bash
docker compose up --build
```
Then open http://localhost:9200.

## Test
```bash
pytest -q --cov=. --cov-report=term-missing
```

## Demo request
```text
Investigate recurring high-severity alarms for Boiler Feed Pump 101 over the last 90 days, identify likely contributing factors, retrieve the relevant operating procedure, and recommend actions.
```

## Architecture
See `docs/architecture.md` and `docs/architecture-diagram.svg`.

## MCP
The copilot never calls the Alarm API directly. It discovers tools from the MCP server and invokes them through the MCP JSON-RPC tool interface. See `docs/mcp-tool-catalog.md`.

## RAG
Run `python -m rag.ingestion.build_index` to ingest the included synthetic corpus. See `docs/rag-design.md`.

## Security
Never commit `.env`, tokens, API keys, certificates or restricted plant documents. The supplied `demo-token` is only for local simulation.

## Demo video
Record a <=10 minute walkthrough covering: successful investigation, MCP tool discovery/execution trace, RAG citations, and one degraded/error case. Add the final link here before submission.

## Submission checklist
- [ ] `docker compose up --build` works
- [ ] GUI works
- [ ] MCP tool discovery visible
- [ ] Combined MCP + RAG scenario works
- [ ] Citations visible
- [ ] Tests pass
- [ ] Architecture diagram included
- [ ] `.env` not committed
- [ ] Demo video linked
- [ ] GitHub Actions passes
