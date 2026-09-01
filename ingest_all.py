# ingest_all.py
"""
Full ingestion pipeline runner — supports both full and single-scheme re-ingest.

Usage:
  # Refresh ALL 5 HDFC schemes (full run):
  python ingest_all.py

  # Refresh a SINGLE scheme only:
  python ingest_all.py --url "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth"

  # Dry-run — scrape + chunk only, no ChromaDB writes:
  python ingest_all.py --dry-run
  python ingest_all.py --dry-run --url "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"

Called by GitHub Actions workflows (daily_update.yml and manual_ingest.yml).
"""
import argparse
import json
import logging
import sys
from pathlib import Path

from config import SCHEME_URLS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("ingest_all")


def _dry_run(urls: list[str]) -> None:
    """Scrape and chunk only — no ChromaDB writes, no metadata.json update."""
    from ingestion.scraper import scrape_scheme
    from ingestion.chunker import chunk_document
    from playwright.sync_api import sync_playwright

    logger.info("=== DRY RUN — scrape + chunk only, no ChromaDB writes ===")

    results = []
    with sync_playwright() as pw:
        for url in urls:
            slug = url.rstrip("/").split("/")[-1]
            logger.info("[%s] Scraping %s …", slug, url)
            try:
                scraped = scrape_scheme(url, playwright_instance=pw)
                chunks = chunk_document(
                    text=scraped["content"],
                    source_url=url,
                    scrape_date=scraped["scraped_at"],
                    scheme_name=scraped["scheme_name"],
                )
                non_noise = [c for c in chunks if c.get("chunk_type") != "noise"]
                logger.info(
                    "[%s] \u2705  %d total chunks, %d non-noise (dry run — no write)",
                    slug, len(chunks), len(non_noise),
                )
                results.append({
                    "slug": slug,
                    "scheme_name": scraped["scheme_name"],
                    "total_chunks": len(chunks),
                    "non_noise_chunks": len(non_noise),
                    "scrape_date": scraped["scraped_at"],
                })
            except Exception as exc:
                logger.error("[%s] \u274c  Failed: %s", slug, exc, exc_info=True)
                results.append({"slug": slug, "error": str(exc)})

    # Print summary table
    print("\n" + "=" * 60)
    print("DRY RUN SUMMARY")
    print("=" * 60)
    print(f"  {'Scheme':<50} {'Non-Noise':>10}")
    print(f"  {'-'*50} {'-'*10}")
    for r in results:
        if "error" in r:
            print(f"  {r['slug']:<50} {'ERROR':>10}")
        else:
            print(f"  {r['scheme_name']:<50} {r['non_noise_chunks']:>10}")
    print("=" * 60)


def _full_run(urls: list[str]) -> None:
    """Full ingestion: scrape -> chunk -> delete stale -> embed -> update metadata."""
    from scheduler.daily_update import run_daily_update

    summary = run_daily_update(urls=urls)

    # Print GitHub Actions-friendly summary table to stdout
    print("\n" + "=" * 60)
    print(f"INGESTION SUMMARY  [{summary['run_date']}]")
    print("=" * 60)
    print(f"  {'Slug':<50} {'Status':>8}  {'Chunks':>6}")
    print(f"  {'-'*50} {'-'*8}  {'-'*6}")
    for slug, info in summary["schemes"].items():
        status = "OK" if info["status"] == "ok" else "ERROR"
        chunks = info.get("chunks", "-")
        print(f"  {slug:<50} {status:>8}  {chunks!s:>6}")
    print("=" * 60)

    # Exit with code 1 if any scheme failed (GitHub Actions marks job as failed)
    errors = [s for s, v in summary["schemes"].items() if v["status"] == "error"]
    if errors:
        logger.error("The following scheme(s) failed: %s", ", ".join(errors))
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="HDFC Fund data ingestion pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--url",
        default="",
        metavar="URL",
        help=(
            "Re-ingest a single Groww scheme URL. "
            "Omit to refresh all 5 HDFC schemes."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Scrape and chunk only — do NOT write to ChromaDB or metadata.json. "
            "Useful for testing scraper changes."
        ),
    )
    args = parser.parse_args()

    # Determine target URL(s)
    if args.url:
        urls = [args.url]
        logger.info("Single-scheme mode: %s", args.url)
    else:
        urls = list(SCHEME_URLS)
        logger.info("Full-refresh mode: %d schemes", len(urls))

    if args.dry_run:
        _dry_run(urls)
    else:
        _full_run(urls)


if __name__ == "__main__":
    main()
