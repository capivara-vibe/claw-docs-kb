# Contributing to ClawDocs

Thanks for your interest in contributing! This is a small utility project — contributions are welcome.

## How to Contribute

### Reporting Issues

- Search existing issues before opening a new one.
- Use the appropriate issue template (bug report or feature request).
- Include the Python version, OS, and full error output when reporting bugs.

### Pull Requests

1. Fork the repo and create a branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Make your changes. Keep commits focused and atomic.
3. Commit messages: imperative mood, ≤72 chars (`Add rate-limit retry logic`).
4. Open a PR against `main` and fill out the PR template.

### Code Style

- **Formatter**: [`ruff format`](https://docs.astral.sh/ruff/) — 4-space indentation.
- **Linter**: `ruff check` — no warnings allowed.
- **Type hints**: strongly preferred on all function signatures.
- Comments explain *why*, not *what*.

### Running Locally

```bash
uv run scrape_docs.py
```

## Scope

This project is intentionally minimal. Before adding new dependencies or expanding scope significantly, please open an issue to discuss.
