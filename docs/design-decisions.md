# Design Decisions

1. **One vertical slice over breadth.** The primary scenario proves MCP + RAG together.
2. **Structured vs unstructured separation.** Alarm facts come from the API; procedures come from RAG.
3. **Deterministic default mode.** The project runs without cloud credentials. An optional LLM adapter can be added without changing the MCP or RAG contracts.
4. **No direct API calls from orchestration.** The copilot uses MCP client calls only.
5. **No write tools.** The scenario is read/analysis only, avoiding unsafe side effects.
6. **Traceability first.** Every MCP call is visible in the GUI with duration and status.

7. **Recurrence-driven investigation.** High/Critical alarms are grouped by alarm name and ranked by occurrence count before downstream correlation, recommendations, priority scoring and RAG retrieval; this prevents an arbitrary first alarm from driving the investigation.
