---
name: manage-notebooks
description: "Allows the agent to interact with the NotebookLM MCP server to create, query, and manage notebooks."
---

# Skill: Manage NotebookLM Notebooks

## Overview
This skill provides instructions on how to leverage the NotebookLM MCP integration to perform advanced reasoning and context grounding.

## Prerequisites
- The `notebooklm-mcp-server` must be installed and authenticated. 
- You can verify this by checking if tools like `notebook_list` exist in your available MCP tools list.

## Usage Scenarios
- **Research:** Use `notebook_create` to spawn a new workspace. Ingest URLs via `notebook_add_url` or static text via `notebook_add_text`.
- **Querying Insight:** When the user asks complex questions regarding large context, pass the queries to `notebook_query` against the created notebook's UUID. This leverages Google's Gemini 1.5 Pro models specialized for grounding.
- **Content Generation:** Instead of drafting artifacts yourself, you can ask the NotebookLM MCP to generate study materials using `audio_overview_create`, `slide_deck_create`, or `report_create` if it aligns with the user's goals.

## Important Limits
- NotebookLM has a limit of up to 50 sources per notebook.
- Each source has a character limit (~500k words).

## Example Pattern

1. **List existing notebooks:**
   ```
   notebook_list()
   ```
2. **Determine or create a target:**
   ```
   notebook_create(title="My Research Project")
   ```
3. **Add some source data:**
   ```
   notebook_add_text(notebook_id="<uuid>", title="Excerpt", text="It was the best of times...")
   ```
4. **Query the data:**
   ```
   notebook_query(notebook_id="<uuid>", query="What times were they?")
   ```
