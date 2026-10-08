# MCP Tool Catalog

| Tool | Purpose | Required input | Source operation |
|---|---|---|---|
| search_assets | Resolve asset names/types | query | GET /assets/search |
| get_asset_metadata | Asset context and related assets | asset_id | GET /assets/{asset_id}/metadata |
| get_alarms | Historical/active alarms | filters + pagination | GET /alarms |
| get_alarm_summary | KPI/grouped alarm summary | scope/time/grouping | POST /alarms/summary |
| get_alarm_trends | Trend points | scope/time/bucket | POST /alarms/trends |
| correlate_alarms | Co-occurrence analysis | asset_ids/time window | POST /alarms/correlation |
| score_alarm_priority | Priority and factors | alarm_id | POST /alarms/priority-score |
| get_operator_recommendations | Operator actions/context | alarm_id | POST /recommendations/operator-actions |
| get_rationalization_candidates | Recurring/nuisance candidates | scope/threshold | POST /alarms/rationalization-candidates |

All tools use typed JSON schemas, validate required inputs, propagate trace metadata and map source-system errors into MCP errors. The MCP endpoint supports `initialize`, `tools/list`, and `tools/call` JSON-RPC operations.
