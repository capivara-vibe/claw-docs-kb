---
description: Pipeline to build a NotebookLM database seeded with fresh web data via Perplexity MCP
---

# `seed-notebook` Workflow

## Overview
This workflow automates the creation of a new **NotebookLM** notebook, pre-populated with fresh internet research obtained via the **Perplexity MCP**. It uses a Draft → Critique → Refine asynchronous execution model.

## Steps

1. **Understand Request & Ask Perplexity**
   When the user requests a new notebook on a specific topic, the Agent will first leverage the `mcp_perplexity-ask_perplexity_ask` tool.
   - Example prompt to the Perplexity tool: "Provide a comprehensive, up-to-date summary and the 5 most important current URLs regarding [Topic]. Format the response clearly."

2. **Draft the Implementation Plan**
   The Agent will construct an `implementation_plan.md` using the data gathered from Perplexity. The plan must clearly state:
   - What the Notebook's title will be.
   - What text will be injected (derived from Perplexity summary).
   - What URLs will be injected (derived from Perplexity sources).
   
3. **Notify User for Approval**
   The Agent will use the `notify_user` tool, attaching the `implementation_plan.md`, asking for approval to proceed.

4. **Execute (Notebook Creation & Ingestion)**
   Once approved, the Agent runs the following via the NotebookLM MCP:
   - `notebook_create(title="...")` -> Returns UUID.
   - For the summary text: `notebook_add_text(notebook_id=UUID, text="...")`
   - For all URLs: `notebook_add_url(notebook_id=UUID, url="...")`

5. **Verify**
   - Query the new notebook (`notebook_query(notebook_id=UUID)`) with a simple test question to verify grounding.
   - Update `task.md` and notify the user of success.
