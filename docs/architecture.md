# Architecture

## Runtime flow
1. User enters a natural-language alarm investigation request in the GUI.
2. Copilot backend creates a trace ID and asks the candidate-developed MCP server for its tool catalog.
3. The orchestrator resolves the asset and retrieves historical alarms through MCP, filters to High/Critical events, groups by alarm name, ranks recurrence, and uses the top recurring alarms to focus correlation, priority, operator recommendations and RAG retrieval.
4. The RAG service retrieves relevant operating-procedure, maintenance and troubleshooting passages from the local corpus.
5. The orchestrator combines structured alarm evidence with document evidence and produces a grounded response.
6. GUI renders the answer, citations and MCP execution trace.

## Boundaries
- Alarm API simulator: deterministic enterprise source-system stand-in, based on the supplied Postman contract.
- MCP server: integration boundary. It owns source-system authentication, error mapping, retry behavior and trace propagation.
- Copilot: planning/orchestration layer. It never calls the Alarm API directly.
- RAG: unstructured evidence retrieval only; structured alarm facts remain in the Alarm API path.
- GUI: presentation and traceability.

## Security
Secrets are environment variables; retrieved documents are untrusted reference material; no write-capable tools are exposed; logs do not contain bearer tokens.
