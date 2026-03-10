# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "beautifulsoup4",
#     "markdownify",
# ]
# ///

"""
ClawDocs scraper — fetches, parses, and merges the OpenClaw documentation
into clean, category-organized Markdown files for AI ingestion.

Usage:
    uv run scrape_docs.py [--output-dir <path>] [--batch-size <n>] [--dry-run]

Env vars (all optional):
    CLAWD_OUTPUT_DIR    Override the output directory
    CLAWD_BATCH_SIZE    Override concurrent request batch size
    CLAWD_TIMEOUT       HTTP timeout in seconds (default: 30)
"""

import argparse
import re
import asyncio
import logging
import os
import shutil
import xml.etree.ElementTree as ET
from urllib.robotparser import RobotFileParser
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("clawd")


# ---------------------------------------------------------------------------
# Config / defaults (overridable via env or CLI)
# ---------------------------------------------------------------------------
SITEMAP_URL = "https://docs.openclaw.ai/sitemap.xml"
ROBOTS_TXT_URL = "https://docs.openclaw.ai/robots.txt"
CHANGELOG_URL = "https://raw.githubusercontent.com/openclaw/openclaw/main/CHANGELOG.md"
DEFAULT_OUTPUT_DIR = Path(os.getenv("CLAWD_OUTPUT_DIR", "openclaw-docs-merged"))
DEFAULT_BATCH_SIZE = int(os.getenv("CLAWD_BATCH_SIZE", "15"))
DEFAULT_TIMEOUT = float(os.getenv("CLAWD_TIMEOUT", "30"))
BATCH_DELAY = 0.5  # seconds between batches — be polite

# URL path segments that should be excluded from scraping
EXCLUDE_PATTERNS = [
    "/ja-JP",
    "/zh-CN",
    "/platforms/ios",
    "/platforms/mac",
]

# Sitemap XML namespace
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

# HTTP headers to identify the scraper politely
HEADERS = {
    "User-Agent": "ClawDocs-Scraper/1.0 (https://github.com/capivara-vibe/claw-docs-kb)",
}

# Compiled regexes for clean_markdown (compiled once, used per page)
_RE_ANCHOR_HEADER = re.compile(r"\[\u200b?\]\(#[^)]*\)\s*")
_RE_COPY_BUTTON = re.compile(r"^Copy\n(?=```)", re.MULTILINE)
_RE_REMOTE_IMAGE = re.compile(r"!\[[^\]]*\]\(https?://[^)]+\)\s*")
_RE_CARD_LINK = re.compile(r"\[##\s*(.+?)\n(.+?)\]\((/[^)]+)\)")
_RE_ORPHAN_STEP = re.compile(r"^(\d+)\n(?=\S)", re.MULTILINE)


def clean_markdown(text: str) -> str:
    """Post-process markdownify output to strip Mintlify rendering noise.

    Optimized for AI/RAG consumption — every remaining byte should carry
    semantic value.
    """
    text = _RE_ANCHOR_HEADER.sub("", text)
    text = _RE_COPY_BUTTON.sub("", text)
    text = _RE_REMOTE_IMAGE.sub("", text)
    text = _RE_CARD_LINK.sub(r"- **\1** — \2 → \3", text)
    text = _RE_ORPHAN_STEP.sub(r"**Step \1.** ", text)
    return text


def trim_changelog(text: str, max_releases: int) -> str:
    """Keep only the first *max_releases* versioned release sections."""
    lines = text.splitlines(keepends=True)
    kept: list[str] = []
    release_count = 0
    for line in lines:
        # Each release starts with '## <version>' (not '## Unreleased')
        if line.startswith("## ") and not line.strip().endswith("Unreleased"):
            release_count += 1
            if release_count > max_releases:
                break
        kept.append(line)
    return "".join(kept)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def should_exclude(url: str) -> bool:
    """Return True if any exclude pattern is found in the URL path."""
    return any(pattern in url for pattern in EXCLUDE_PATTERNS)


def get_category(url: str) -> str:
    """Derive a category name from the first path segment of a URL."""
    path = urlparse(url).path.strip("/")
    if not path:
        return "index"
    return path.split("/")[0]


# ---------------------------------------------------------------------------
# Core fetch logic
# ---------------------------------------------------------------------------
async def fetch_and_convert(
    client: httpx.AsyncClient,
    url: str,
    retries: int = 3,
    backoff: float = 2.0,
) -> tuple[str, str, str] | None:
    """
    Fetch a doc page and convert it to Markdown.

    Returns (category, url, markdown) or None on failure.
    Retries on transient network / 5xx errors with exponential backoff.
    """
    if should_exclude(url):
        return None

    for attempt in range(1, retries + 1):
        try:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Mintlify docs use .prose for main content — avoids nav/sidebar noise
            main_content = (
                soup.select_one(".prose")
                or soup.find("main")
                or soup.find("article")
                or soup.body
            )

            md_content = markdownify(str(main_content), heading_style="ATX")

            # Collapse excessive blank lines
            md_content = "\n".join(
                line for line in md_content.splitlines() if line.strip()
            )

            # Strip Mintlify rendering noise for RAG
            md_content = clean_markdown(md_content)

            category = get_category(url)
            log.info("✅ %s  →  %s", url, category)
            return category, url, md_content

        except httpx.TimeoutException:
            log.warning("⏱ Timeout on %s (attempt %d/%d)", url, attempt, retries)
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            # Don't retry client errors (4xx) — they won't resolve themselves
            if 400 <= status < 500:
                log.warning("❌ HTTP %d — skipping %s", status, url)
                return None
            log.warning(
                "⚠️ HTTP %d on %s (attempt %d/%d)", status, url, attempt, retries
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("⚠️ Error on %s (attempt %d/%d): %s", url, attempt, retries, exc)

        if attempt < retries:
            await asyncio.sleep(backoff**attempt)

    log.error("❌ Gave up on %s after %d attempts", url, retries)
    return None


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
async def run(
    output_dir: Path,
    batch_size: int,
    timeout: float,
    clean: bool,
    dry_run: bool,
    changelog_releases: int = 5,
) -> None:
    log.info("🚀 ClawDocs scraper starting")
    log.info("   Output dir : %s", output_dir)
    log.info("   Batch size : %d", batch_size)
    log.info("   Timeout    : %.1fs", timeout)

    async with httpx.AsyncClient(timeout=timeout, headers=HEADERS) as client:
        # -- Check robots.txt compliance ------------------------------------
        log.info("⚖️  Checking robots.txt compliance...")
        try:
            robots_resp = await client.get(ROBOTS_TXT_URL, follow_redirects=True)
            robots_resp.raise_for_status()
            rp = RobotFileParser()
            rp.parse(robots_resp.text.splitlines())
            if not rp.can_fetch(HEADERS["User-Agent"], SITEMAP_URL):
                log.critical(
                    "🛑 robots.txt explicitly forbids us from crawling. Aborting legally."
                )
                raise SystemExit(1)
            log.info("✅ robots.txt authorizes scraping.")
        except httpx.HTTPError as e:
            log.warning(
                "⚠️ Could not fetch robots.txt (%s). Assuming implicit permission.", e
            )

        # -- Fetch sitemap --------------------------------------------------
        log.info("🗺️  Fetching sitemap: %s", SITEMAP_URL)
        sitemap_resp = await client.get(SITEMAP_URL)
        sitemap_resp.raise_for_status()

        root = ET.fromstring(sitemap_resp.text)
        urls = [
            elem.text for elem in root.findall(".//sm:loc", SITEMAP_NS) if elem.text
        ]
        log.info("🔍 Found %d URLs in sitemap", len(urls))

        if dry_run:
            log.info("🏜️  Dry run — not writing any files.")
            for url in urls:
                excluded = should_exclude(url)
                log.info("  %s %s", "SKIP" if excluded else "  OK", url)
            return

        # -- Prepare output dir ---------------------------------------------
        if clean and output_dir.exists():
            log.info("🧹 Cleaning output dir: %s", output_dir)
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # -- Scrape in batches ----------------------------------------------
        merged_docs: dict[str, list[tuple[str, str]]] = defaultdict(list)
        total = len(urls)

        for i in range(0, total, batch_size):
            batch = urls[i : i + batch_size]
            tasks = [fetch_and_convert(client, url) for url in batch]
            results = await asyncio.gather(*tasks)

            for res in results:
                if res:
                    cat, url, md = res
                    merged_docs[cat].append((url, md))

            done = min(i + batch_size, total)
            log.info("⏳ Progress: %d / %d", done, total)

            # Be polite — pause between batches
            if done < total:
                await asyncio.sleep(BATCH_DELAY)

        # -- Write merged files ---------------------------------------------
        log.info("💾 Writing %d category files…", len(merged_docs))
        for category, pages in sorted(merged_docs.items()):
            out_path = output_dir / f"{category}.md"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"# Category: {category.upper()}\n")
                f.write("> *Data scraped from OpenClaw (MIT Licensed).*\n\n")

                # Sort by URL for deterministic, diffable output
                for url, md in sorted(pages, key=lambda x: x[0]):
                    f.write(f"\n\n---\n## Source: {url}\n\n")
                    f.write(md)
            log.info("📚 %s  (%d pages)", out_path, len(pages))

        # -- Fetch changelog ------------------------------------------------
        log.info("📋 Fetching changelog…")
        changelog_resp = await client.get(CHANGELOG_URL, follow_redirects=True)
        changelog_resp.raise_for_status()
        changelog_text = changelog_resp.text
        if changelog_releases > 0:
            changelog_text = trim_changelog(changelog_text, changelog_releases)
            log.info("✂️  Trimmed changelog to %d releases", changelog_releases)
        changelog_path = output_dir / "changelog.md"
        changelog_path.write_text(changelog_text, encoding="utf-8")
        log.info("📚 %s", changelog_path)

    log.info("🎉 Done! Output: %s", output_dir.resolve())


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape and merge OpenClaw docs into per-category Markdown files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to write merged Markdown files into.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Number of concurrent HTTP requests per batch.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="HTTP request timeout in seconds.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        default=False,
        help="Delete the output directory before scraping (ensures no stale files).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print what would be scraped without writing any files.",
    )
    parser.add_argument(
        "--changelog-releases",
        type=int,
        default=5,
        help="Keep only the N most recent releases in changelog.md (0 = keep all).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        asyncio.run(
            run(
                output_dir=args.output_dir,
                batch_size=args.batch_size,
                timeout=args.timeout,
                clean=args.clean,
                dry_run=args.dry_run,
                changelog_releases=args.changelog_releases,
            )
        )
    except KeyboardInterrupt:
        log.info("Interrupted.")
    except Exception as exc:
        log.critical("💥 Fatal error: %s", exc, exc_info=True)
        raise SystemExit(1) from exc
