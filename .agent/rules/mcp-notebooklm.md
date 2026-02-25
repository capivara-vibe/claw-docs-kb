---
activation: always
---

# NotebookLM MCP Standard Operating Procedures

## Capability Usage
When instructed to research, summarize, or cross-reference data:
1. Try utilizing the `notebook_list` tool to identify existing knowledge bases before creating new ones unnecessarily.
2. If given URLs, use `notebook_add_url` to ingest them. Follow up by confirming ingestion success.
3. Use `notebook_add_text` or `notebook_add_drive` for raw data ingestion.
4. Execute heavy reasoning queries using the `notebook_query` tool to leverage NotebookLM's capabilities.
5. If creating resources for the user like study guides, try tools like `audio_overview_create`, `quiz_create`, or `flashcards_create` if appropriate for the task request.

## Authentication State
If the server throws authentication errors, notify the user that they must rerun `notebooklm-mcp-auth` to refresh their Chrome headless session, or use the `refresh_auth` tool if the cached session hasn't expired.
