# Copilot Instructions for ClawDocs

## Project Overview

**ClawDocs** is an async documentation scraper written in Python. It fetches, parses, and merges the official [OpenClaw](https://docs.openclaw.ai) documentation into clean, category-organized Markdown files optimized for AI ingestion (NotebookLM, RAG pipelines, LLM context windows).

The entire scraper lives in a single file: `scrape_docs.py`.

## Tech Stack

- **Language**: Python ≥ 3.11
- **Package/run manager**: [`uv`](https://github.com/astral-sh/uv) — dependencies are declared as inline PEP 723 metadata at the top of `scrape_docs.py`
- **HTTP client**: `httpx` (async)
- **HTML parser**: `beautifulsoup4`
- **Markdown converter**: `markdownify`
- **Linter/formatter**: `ruff`

## Running the Project

```bash
# Standard run
uv run scrape_docs.py

# Validate without writing files (use this in CI / for quick checks)
uv run scrape_docs.py --dry-run

# Clean output dir before run
uv run scrape_docs.py --clean
```

## Lint & Format

```bash
uv tool run ruff check .       # must pass with zero warnings
uv tool run ruff format .      # 4-space indentation, auto-formatted
```

Always run both commands before opening a PR. The CI workflow (`ci.yml`) enforces both.

## Code Conventions

- **Type hints** are required on all function signatures.
- Comments explain *why*, not *what*.
- Commit messages use imperative mood, ≤ 72 characters (e.g., `Add retry logic for 5xx responses`).
- Keep the scraper minimal — prefer extending `scrape_docs.py` over adding new files. Discuss scope expansions in an issue first.
- Do not add new top-level dependencies without discussing in an issue first.
- Never commit secrets, API keys, or scraped output files (`openclaw-docs-merged/`).

## Testing

There is no formal test suite. The canonical validation step is a dry run:

```bash
uv run scrape_docs.py --dry-run
```

This must complete without errors. The CI job (`lint-and-test` in `.github/workflows/ci.yml`) runs this automatically on every PR.

## Repository Layout

```
scrape_docs.py              # The entire scraper (single-file)
.agent/
  rules/                    # Always-on agent rules (e.g., NotebookLM MCP SOPs)
  skills/                   # Reusable agent skill definitions
  workflows/                # Step-by-step agent workflow guides
.github/
  workflows/ci.yml          # Lint + dry-run CI
  PULL_REQUEST_TEMPLATE.md  # PR checklist
CONTRIBUTING.md             # Contribution guidelines
```

## Agent Configuration (`.agent/`)

The `.agent/` directory contains instructions used by the Copilot coding agent:

- **`.agent/rules/`** — rules with `activation: always` are loaded on every agent session.
- **`.agent/skills/`** — opt-in capabilities (e.g., `manage-notebooks` for NotebookLM MCP).
- **`.agent/workflows/`** — multi-step workflow guides the agent can follow (e.g., `update-docs`, `seed-notebook`).

When working on tasks related to NotebookLM or documentation ingestion, consult `.agent/rules/mcp-notebooklm.md` and `.agent/skills/manage-notebooks/SKILL.md`.
