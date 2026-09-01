# ingestion/scraper.py
"""
Playwright-based scraper for HDFC mutual fund scheme pages on Groww.

Groww is a React/Next.js app — static requests return an empty shell.
Playwright renders the full page before extracting content.

Usage:
    from ingestion.scraper import scrape_all
    items = scrape_all()

Each returned dict has:
    slug, url, scraped_at, scheme_name, fields (dict of extracted facts), content (full text)
"""
import datetime
import re
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from bs4 import BeautifulSoup

from config import SCHEME_URLS, WHITELISTED_DOMAINS

RAW_DIR = Path("data/raw")

# ── Selector constants ────────────────────────────────────────────────────────
# These are best-effort CSS selectors for Groww's current layout (Aug 2026).
# Groww may change their DOM; the scraper degrades gracefully to full-page text.

_WAIT_SELECTOR   = "h1"          # element that proves JS has rendered
_PAGE_TIMEOUT_MS = 30_000        # 30 s per page
_SCROLL_PAUSE_MS = 1_500         # wait after scroll to let lazy content load

# Text-level patterns used to locate fact rows in the rendered text.
# These are tuned to Groww's actual rendered text layout (Aug 2026).
# Pattern order matters — more specific patterns first.
_FACT_PATTERNS = {
    # "Expense Ratio of HDFC XYZ Fund is 1.19% as of..."
    "expense_ratio": re.compile(
        r"Expense Ratio of .+? is ([0-9]+\.?[0-9]*\s*%)", re.I
    ),
    # "Exit load\nNil" or "Exit load\n1% if redeemed within 1 year"
    "exit_load": re.compile(
        r"^Exit [Ll]oad\s*\n([^\n]+)", re.I | re.MULTILINE
    ),
    # "Minimum SIP Investment is set to ₹500"
    "min_sip": re.compile(
        r"Minimum SIP Investment is (?:set to )?[₹Rs.\s]*([0-9,]+)", re.I
    ),
    # "Minimum Lumpsum Investment is ₹500"
    "min_lumpsum": re.compile(
        r"Minimum Lumpsum Investment is [₹Rs.\s]*([0-9,]+)", re.I
    ),
    # "Very High Risk" / "High Risk" / "Moderately High Risk" near h1 area
    "risk": re.compile(
        r"\b(Very High Risk|High Risk|Moderately High Risk|Moderate Risk|Low to Moderate Risk|Low Risk)\b",
        re.I
    ),
    # "Fund benchmark\nNIFTY 500 Total Return Index"
    "benchmark": re.compile(
        r"^Fund benchmark\s*\n([^\n]+)", re.I | re.MULTILINE
    ),
    # "Amar Kalkundrikar is the Current Fund Manager"
    "fund_manager": re.compile(
        r"([A-Z][a-zA-Z\s]+?) is the (?:Current )?Fund Manager", re.I
    ),
    # "ELSS – 3Y Lock-in" badge near h1
    "lock_in": re.compile(
        r"ELSS[^|\n]*?(\d+\s*Y(?:ear)?(?:\s*Lock-?in)?)", re.I
    ),
    # "Category average (Equity ELSS)" or "Category (Equity Mid Cap)"
    "category": re.compile(
        r"Category average \(([^)]+)\)|Category\s*\|\s*([^\n|]+)", re.I
    ),
}


def is_allowed(url: str) -> bool:
    """Return True if the URL's domain is in the whitelist."""
    return any(d in urlparse(url).netloc for d in WHITELISTED_DOMAINS)


def _extract_fields(text: str) -> dict:
    """
    Run regex patterns over the full page text to extract key factual fields.
    Returns a dict with whatever fields could be found (missing → None).
    """
    fields = {}
    for key, pattern in _FACT_PATTERNS.items():
        match = pattern.search(text)
        if match:
            # Some patterns have multiple groups (alternatives); pick first non-None
            value = next((g for g in match.groups() if g), None)
            fields[key] = value.strip() if value else None
        else:
            fields[key] = None
    return fields


def _clean_text(raw_text: str) -> str:
    """
    Light-touch cleaning of Playwright-extracted page text:
    - Collapse 3+ consecutive blank lines to 2
    - Strip leading/trailing whitespace from each line
    - Remove purely numeric lines (nav/pagination artifacts)
    - Deduplicate consecutive identical lines
    """
    lines = raw_text.splitlines()
    cleaned = []
    blank_count = 0
    prev_line = None

    for line in lines:
        line = line.strip()

        # Skip pure numbers (page nav, JS artifacts)
        if re.fullmatch(r"\d+", line):
            continue

        # Collapse blank lines
        if not line:
            blank_count += 1
            if blank_count <= 2:
                cleaned.append("")
            continue

        blank_count = 0

        # Deduplicate consecutive identical lines
        if line == prev_line:
            continue

        cleaned.append(line)
        prev_line = line

    return "\n".join(cleaned).strip()


def _build_structured_text(scheme_name: str, url: str, fields: dict, full_text: str) -> str:
    """
    Build a clean, factual text document from extracted fields + full page text.
    Factual fields are placed at the top so chunking always captures them.
    """
    header_lines = [
        f"Scheme: {scheme_name}",
        f"Source: {url}",
        "",
    ]

    # Add any extracted structured facts at the top
    field_labels = {
        "category":      "Fund Category",
        "expense_ratio": "Expense Ratio",
        "exit_load":     "Exit Load",
        "min_sip":       "Minimum SIP Amount",
        "min_lumpsum":   "Minimum Lump Sum",
        "risk":          "Riskometer / Risk Level",
        "benchmark":     "Benchmark Index",
        "fund_manager":  "Fund Manager",
        "lock_in":       "Lock-in Period",
    }
    for key, label in field_labels.items():
        value = fields.get(key)
        if value:
            header_lines.append(f"{label}: {value}")

    header_lines.append("")
    header_lines.append("--- Full Page Content ---")
    header_lines.append("")

    return "\n".join(header_lines) + "\n" + full_text


def scrape_scheme(url: str, playwright_instance=None) -> dict:
    """
    Scrape a single Groww scheme page using Playwright.

    Args:
        url:                 Groww scheme page URL (must be whitelisted).
        playwright_instance: An active sync_playwright() context. If None,
                             a new one is created (slower for batches).

    Returns:
        dict with: url, slug, scraped_at, scheme_name, fields, content
    """
    assert is_allowed(url), f"Domain not whitelisted: {url}"

    slug = url.rstrip("/").split("/")[-1]
    scraped_at = datetime.date.today().isoformat()

    # ── Launch browser if not provided ────────────────────────────────────────
    _own_pw = playwright_instance is None
    pw = playwright_instance or sync_playwright().start()

    try:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            locale="en-IN",
        )
        page = context.new_page()

        print(f"  [scraper] Navigating: {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=_PAGE_TIMEOUT_MS)

        # Wait for React to hydrate — h1 is a good signal
        try:
            page.wait_for_selector(_WAIT_SELECTOR, timeout=_PAGE_TIMEOUT_MS)
        except PWTimeout:
            print(f"  [scraper] Warning: h1 not found in time for {slug}, proceeding anyway")

        # Scroll to bottom to trigger lazy-loaded sections
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(_SCROLL_PAUSE_MS)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        # ── Capture raw HTML ──────────────────────────────────────────────────
        html_content = page.content()
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        (RAW_DIR / f"{slug}.html").write_text(html_content, encoding="utf-8")

        # ── Extract scheme name from h1 ───────────────────────────────────────
        scheme_name = slug.replace("-", " ").title()
        try:
            h1_el = page.query_selector("h1")
            if h1_el:
                scheme_name = (h1_el.inner_text() or scheme_name).strip()
        except Exception:
            pass

        # ── Parse with BeautifulSoup for clean text ───────────────────────────
        soup = BeautifulSoup(html_content, "lxml")

        # Remove noise: scripts, styles, nav, footer, cookie banners
        for tag in soup.find_all(["script", "style", "nav", "footer",
                                   "noscript", "svg", "iframe"]):
            tag.decompose()

        raw_text = soup.get_text(separator="\n", strip=True)
        clean_text = _clean_text(raw_text)

        # ── Extract structured fields ─────────────────────────────────────────
        fields = _extract_fields(clean_text)

        # ── Build final document text ─────────────────────────────────────────
        content = _build_structured_text(scheme_name, url, fields, clean_text)

        browser.close()

    finally:
        if _own_pw:
            pw.stop()

    n_fields = sum(1 for v in fields.values() if v)
    print(f"  [scraper] [OK] {slug} | {len(content):,} chars | {n_fields}/{len(fields)} fields extracted")

    return {
        "url":         url,
        "slug":        slug,
        "scraped_at":  scraped_at,
        "scheme_name": scheme_name,
        "fields":      fields,
        "content":     content,
    }


def scrape_all() -> list[dict]:
    """
    Scrape all 5 HDFC scheme pages, reusing one Playwright instance for speed.

    Returns:
        List of scheme dicts (one per URL). Failed pages are skipped with a warning.
    """
    results = []
    print(f"[scraper] Starting scrape of {len(SCHEME_URLS)} scheme pages...\n")

    with sync_playwright() as pw:
        for url in SCHEME_URLS:
            try:
                data = scrape_scheme(url, playwright_instance=pw)
                results.append(data)
            except Exception as exc:
                print(f"  [scraper] [FAIL] ({url}): {exc}")

    print(f"\n[scraper] Done. {len(results)}/{len(SCHEME_URLS)} pages scraped successfully.")
    return results


if __name__ == "__main__":
    items = scrape_all()
    for item in items:
        print(f"\n{item['scheme_name']}")
        for k, v in item["fields"].items():
            if v:
                print(f"  {k}: {v}")
