# RAG Design

## Corpus
- BFP 101 operating procedure
- centrifugal pump maintenance manual
- alarm troubleshooting guide
- refinery alarm philosophy

## Ingestion
Markdown -> section-aware chunks -> TF-IDF index -> JSON artifact. The local TF-IDF implementation is deliberately dependency-light and reproducible. It is an equivalent retrieval approach for this small synthetic corpus; a production deployment can replace it with an embedding/vector service without changing the orchestration contract.

## Metadata
Each chunk records document ID, source filename, section, asset scope and retrieval score.

## Retrieval
Query is generated from the resolved asset, alarm name and investigation intent. Top-ranked non-zero similarity chunks are returned. No-result responses are handled as degraded rather than hallucinated.

## Grounding and injection defense
Retrieved text is reference evidence only. It is never treated as system instructions and cannot change tool permissions, credentials or orchestration rules. The final response exposes document names/sections so evaluators can verify grounding.
