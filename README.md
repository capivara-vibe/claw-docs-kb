# 📚 ClawDocs

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-%3E%3D3.11-brightgreen)](https://www.python.org/)
[![OpenClaw Docs](https://img.shields.io/badge/source-docs.openclaw.ai-orange)](https://docs.openclaw.ai)

> **ClawDocs** is an async documentation scraper that fetches, parses, and merges the official [OpenClaw](https://docs.openclaw.ai) documentation into clean, category-organized Markdown files — optimized for AI ingestion (NotebookLM, RAG pipelines, LLM context windows).

---

## ✨ Features

- Fetches all URLs from the OpenClaw sitemap automatically
- Filters out irrelevant locales and platform-specific pages
- Extracts main prose content (skips navbars, sidebars)
- Groups output by documentation category into single merged `.md` files
- Fetches the live `CHANGELOG.md` directly from the OpenClaw GitHub repo
- Batched async HTTP requests to be polite to the remote server

---

## 🚀 Quick Start

### Prerequisites

- Python ≥ 3.11
- [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip`

### Run with `uv` (zero install friction)

```bash
# Standard run
uv run scrape_docs.py

# Clean output dir first (removes stale files)
uv run scrape_docs.py --clean

# Preview what would be scraped without writing files
uv run scrape_docs.py --dry-run

# Custom output dir, larger batches, longer timeout
uv run scrape_docs.py --output-dir ./my-docs --batch-size 20 --timeout 60
```

`uv` automatically resolves the inline PEP 723 dependencies (`httpx`, `beautifulsoup4`, `markdownify`).

### Run with `pip`

```bash
pip install httpx beautifulsoup4 markdownify
python scrape_docs.py [flags]
```

### All CLI flags

```text
--output-dir PATH   Output directory (default: openclaw-docs-merged)
--batch-size N      Concurrent requests per batch (default: 15)
--timeout SECS      HTTP timeout in seconds (default: 30)
--clean             Delete output dir before run (no stale files)
--dry-run           Print URLs that would be scraped; write nothing
```

---

## 📂 Output Structure

The script writes merged Markdown files to `./openclaw-docs-merged/`:

```text
openclaw-docs-merged/
├── index.md          # Root-level docs
├── setup.md          # Setup & installation pages
├── configuration.md  # Configuration reference
├── plugins.md        # Plugin system docs
├── changelog.md      # Live CHANGELOG from GitHub
└── ...               # One file per top-level doc category
```

---

## ⚙️ Configuration

All tunable values can be set via **CLI flags** (take precedence) or **environment variables**:

| Env var              | CLI flag          | Default                   | Purpose                         |
|----------------------|-------------------|---------------------------|---------------------------------|
| `CLAWD_OUTPUT_DIR`   | `--output-dir`    | `openclaw-docs-merged`    | Output directory                |
| `CLAWD_BATCH_SIZE`   | `--batch-size`    | `15`                      | Concurrent requests per batch   |
| `CLAWD_TIMEOUT`      | `--timeout`       | `30`                      | HTTP timeout (seconds)          |
| —                    | `--clean`         | off                       | Wipe output dir before run      |
| —                    | `--dry-run`       | off                       | Preview only, no writes         |

Hardcoded values (edit `scrape_docs.py` directly):

| Constant           | Default                              | Purpose                          |
|--------------------|--------------------------------------|----------------------------------|
| `SITEMAP_URL`      | `https://docs.openclaw.ai/sitemap.xml` | Source sitemap                 |
| `CHANGELOG_URL`    | GitHub raw CHANGELOG.md URL          | Live changelog source            |
| `EXCLUDE_PATTERNS` | `/ja-JP`, `/zh-CN`, iOS, Mac paths   | URL patterns to skip             |
| `BATCH_DELAY`      | `0.5`                                | Sleep between batches (seconds)  |

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 🔒 Security

See [SECURITY.md](SECURITY.md).

---

## 📄 License

[MIT](LICENSE) © Johan

---

## 🤖 For AI Agents

If you are an AI agent analyzing or interacting with this repository, welcome! Here is some context to help you operate flawlessly here:

1. **Deterministic Output:** `scrape_docs.py` sorts pages by URL before writing to files. This minimizes diff noise, making PRs and historical tracking highly stable.
2. **Issue Tracking (Linear):** We use Linear for project management with bi-directional GitHub sync. To link your work to an issue, prefix your branch name or PR title with the Linear issue key (e.g., `CV-101`). Do *not* close issues manually; merging fixing PRs will auto-transition them.
3. **CI/CD Restrictions:** The `main` branch is strictly protected. Do not attempt direct pushes.
   - Run `uv run scrape_docs.py --dry-run` and `uv tool run ruff check .` locally to ensure the CI (`Lint & Test` workflow) will pass before creating a PR.
4. **Semantic Releases:** We use automated `release-please`. **Always use Conventional Commits** (`feat:`, `fix:`, `docs:`, `chore:`, etc.) so the changelog generation works autonomously.
5. **Context Window Friendly:** The merged Markdown files in `./openclaw-docs-merged/` are designed specifically to be ingested back into RAG, NotebookLM, or standard LLM context windows. They omit noisy HTML like footers and navigation sidebars.
6. **Legal Authority:** The script respects `robots.txt` automation permissions and attributes MIT licensing in every generated output block to remain entirely legally compliant. You are safe to trigger full runs and analyze the subsequent data.
