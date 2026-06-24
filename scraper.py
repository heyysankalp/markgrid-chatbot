"""
markgrid.ai Web Scraper
========================
Crawls the entire markgrid.ai domain using Playwright (headless Chromium),
extracts text content + internal links from every page, and saves results
to markgrid_data.json.

INSTALLATION
------------
1. Install dependencies:
       pip install playwright beautifulsoup4

2. Install Playwright's headless browser (one-time setup):
       playwright install chromium

3. Run the scraper:
       python scraper.py

OUTPUT
------
markgrid_data.json  — one JSON array, one object per crawled page.
"""

import asyncio
import json
import logging
import re
import time
from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


# ─────────────────────────────────────────────
# SECTION 1 — CONFIGURATION
# ─────────────────────────────────────────────
# All tunable knobs live here. Change these if you need to.

BASE_URL        = "https://markgrid.ai"          # Seed URL — where the crawl starts
ALLOWED_DOMAIN  = "markgrid.ai"                  # Only follow links on this domain
OUTPUT_FILE     = "markgrid_data.json"           # Where results are saved
PAGE_TIMEOUT_MS = 30_000                         # Max wait per page (milliseconds)
WAIT_AFTER_LOAD = 2.0                            # Extra seconds to let JS render
DELAY_BETWEEN   = 1.0                            # Polite delay between requests (seconds)

# Tags whose text we skip — navigation, scripts, footers, etc.
SKIP_TAGS = {
    "script", "style", "noscript", "header",
    "footer", "nav", "meta", "head",
}


# ─────────────────────────────────────────────
# SECTION 2 — LOGGING SETUP
# ─────────────────────────────────────────────
# Prints timestamped progress to the terminal so you can watch the crawl live.

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("markgrid-scraper")


# ─────────────────────────────────────────────
# SECTION 3 — URL UTILITIES
# ─────────────────────────────────────────────

def normalise(url: str) -> str:
    """
    Strips URL fragments (#section) and trailing slashes so that
    https://markgrid.ai/about  and  https://markgrid.ai/about/
    are treated as the same page.
    """
    url, _ = urldefrag(url)          # drop #anchor
    return url.rstrip("/")


def is_internal(url: str) -> bool:
    """
    Returns True only if the URL belongs to ALLOWED_DOMAIN.
    Rejects mailto:, tel:, external sites, and non-HTTP schemes.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.netloc.lower()
        # Accept exact match or any subdomain (www.markgrid.ai etc.)
        return host == ALLOWED_DOMAIN or host.endswith("." + ALLOWED_DOMAIN)
    except Exception:
        return False


def should_skip(url: str) -> bool:
    """
    Returns True for URLs we don't want to crawl:
    image files, PDFs, documents, and other non-HTML resources.
    """
    low = url.lower()
    skip_extensions = (
        ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
        ".pdf", ".zip", ".mp4", ".mp3", ".csv", ".xlsx",
        ".docx", ".xml", ".ico",
    )
    return any(low.endswith(ext) for ext in skip_extensions)


# ─────────────────────────────────────────────
# SECTION 4 — CONTENT EXTRACTION
# ─────────────────────────────────────────────

def extract_text(html: str) -> str:
    """
    Uses BeautifulSoup to pull only the visible, meaningful text
    from a rendered HTML page. Strips scripts, styles, nav, etc.
    Collapses whitespace so the output is clean for RAG ingestion.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted tag blocks entirely
    for tag in soup(list(SKIP_TAGS)):
        tag.decompose()

    # Get all remaining text and clean it up
    raw_text = soup.get_text(separator=" ")

    # Collapse multiple spaces/newlines into single spaces
    clean_text = re.sub(r"\s+", " ", raw_text).strip()

    return clean_text


def extract_links(html: str, current_url: str) -> list[str]:
    """
    Finds every <a href="..."> on the page, converts relative URLs
    to absolute ones, and returns only internal links.
    """
    soup = BeautifulSoup(html, "html.parser")
    links = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()

        # Convert relative → absolute  (e.g. /about → https://markgrid.ai/about)
        absolute = urljoin(current_url, href)
        absolute  = normalise(absolute)

        if is_internal(absolute) and not should_skip(absolute):
            links.append(absolute)

    return list(set(links))   # deduplicate within this page


# ─────────────────────────────────────────────
# SECTION 5 — PAGE SCRAPER (async)
# ─────────────────────────────────────────────

async def scrape_page(page, url: str) -> dict | None:
    """
    Navigates Playwright to `url`, waits for JS to settle,
    then extracts title + text + links.
    Returns a dict on success, None on failure.
    """
    try:
        log.info(f"  Fetching → {url}")

        # Navigate and wait until network is quiet
        await page.goto(url, timeout=PAGE_TIMEOUT_MS, wait_until="networkidle")

        # Extra buffer for late-loading JS components
        await asyncio.sleep(WAIT_AFTER_LOAD)

        # Grab the fully-rendered HTML from the live DOM
        html = await page.content()

        title = (await page.title()).strip()
        text  = extract_text(html)
        links = extract_links(html, url)

        log.info(f"  ✓ Done  | title='{title[:60]}' | chars={len(text)} | links={len(links)}")

        return {
            "url":   url,
            "title": title,
            "text":  text,
            "links": links,
        }

    except PlaywrightTimeout:
        log.warning(f"  ✗ TIMEOUT  → {url}")
        return None

    except Exception as e:
        log.error(f"  ✗ ERROR on {url}: {type(e).__name__}: {e}")
        return None


# ─────────────────────────────────────────────
# SECTION 6 — MAIN CRAWLER LOOP
# ─────────────────────────────────────────────

async def crawl() -> list[dict]:
    """
    BFS (breadth-first) crawl starting from BASE_URL.

    Algorithm:
      1. Seed the queue with the homepage URL.
      2. Pop the next URL from the front of the queue.
      3. Scrape it.
      4. Add any new internal links to the back of the queue.
      5. Repeat until the queue is empty.
    """
    queue:   deque[str] = deque([normalise(BASE_URL)])  # URLs to visit
    visited: set[str]   = set()                          # URLs already seen
    results: list[dict] = []                             # Final data store

    log.info(f"Starting crawl: {BASE_URL}")
    log.info(f"Output will be saved to: {OUTPUT_FILE}")

    async with async_playwright() as pw:
        # Launch headless Chromium — no GUI window
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (compatible; MarkgridScraper/1.0; "
                "+https://markgrid.ai)"
            )
        )
        page = await context.new_page()

        while queue:
            url = queue.popleft()

            # Skip if we've already been here
            if url in visited:
                continue

            visited.add(url)
            page_num = len(visited)
            log.info(f"\n[Page {page_num}] Queue size: {len(queue)}")

            data = await scrape_page(page, url)

            if data:
                results.append(data)

                # Discover new links from this page and add to queue
                for link in data["links"]:
                    norm = normalise(link)
                    if norm not in visited:
                        queue.append(norm)

            # Polite delay — don't hammer the server
            await asyncio.sleep(DELAY_BETWEEN)

        await browser.close()

    log.info(f"\nCrawl complete. Pages scraped: {len(results)}")
    return results


# ─────────────────────────────────────────────
# SECTION 7 — JSON EXPORT
# ─────────────────────────────────────────────

def save_to_json(data: list[dict], path: str) -> None:
    """
    Serialises the list of page dicts to a formatted JSON file.
    Uses indent=2 for human-readable output.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    size_kb = round(len(json.dumps(data)) / 1024, 1)
    log.info(f"Saved {len(data)} pages → {path}  ({size_kb} KB)")


# ─────────────────────────────────────────────
# SECTION 8 — ENTRY POINT
# ─────────────────────────────────────────────

async def main():
    start = time.time()

    results = await crawl()
    save_to_json(results, OUTPUT_FILE)

    elapsed = round(time.time() - start, 1)
    log.info(f"Total time: {elapsed}s")


if __name__ == "__main__":
    asyncio.run(main())
