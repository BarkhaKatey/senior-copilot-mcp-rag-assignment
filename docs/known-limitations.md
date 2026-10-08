# Known Limitations

- The Alarm API is a deterministic simulator and does not represent a real plant source system.
- The default RAG uses local TF-IDF retrieval rather than a remote embedding model.
- The default answer composer is deterministic to keep the assignment runnable without an LLM key. Setting `LLM_PROVIDER=openai` and `OPENAI_API_KEY` enables optional grounded OpenAI-compatible synthesis with deterministic fallback.
- The HTTP MCP implementation intentionally focuses on the assignment's tool discovery/call path (`initialize`, `tools/list`, `tools/call`). A production deployment can switch the transport layer to the organization's approved MCP SDK/transport without changing tool contracts.
- Synthetic documents are included; restricted ABB/plant documents should not be committed.
