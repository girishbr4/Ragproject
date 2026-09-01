# scheduler/daily_update.py
"""
Incremental ChromaDB refresh orchestrator for the GitHub Actions daily scheduler.

Called by ingest_all.py (which is invoked by the GitHub Actions workflow).
Re-uses the existing ingestion stack (scraper -> chunker -> embedder) and adds
incremental ChromaDB refresh logic:

  1. Scrape each scheme URL from Groww via Playwright
  2. Chunk and classify the fresh content
  3. Delete stale ChromaDB chunks for that scheme (by source_url filter)
  4. Embed and insert the fresh chunks
  5. Update data/metadata.json with new scrape_date, chunk_count, last_updated

Works for a subset of URLs (--url flag in ingest_all.py) or all SCHEME_URLS.
"""
import logging
import datetime
import json
from pathlib import Path

import chromadb
from playwright.sync_api import sync_playwright

from ingestion.scraper import scrape_scheme
from ingestion.chunker import chunk_document
from ingestion.embedder import ingest_chunks
from config import SCHEME_URLS, CHROMA_DB_PATH

logger = logging.getLogger("scheduler")

METADATA_PATH = Path("data/metadata.json")
PROCESSED_DIR = Path("data/processed")


def _scheme_slug(url: str) -> str:
    """Derive a stable slug from the Groww URL tail segment."""
    return url.rstrip("/").split("/")[-1]


def _delete_scheme_chunks(collection, slug: str) -> int:
    """
    Delete all ChromaDB documents whose metadata source_url contains the slug.
    This clears stale embeddings before re-ingesting fresh chunks.

    Returns the number of documents deleted.
    """
    try:
        existing = collection.get(where={"source_url": {"$contains": slug}})
        ids = existing.get("ids", [])
        if ids:
            collection.delete(ids=ids)
            logger.info("[%s] Deleted %d stale chunk(s) from ChromaDB.", slug, len(ids))
            return len(ids)
    except Exception as exc:
        # $contains may not be supported in all ChromaDB versions — fall back
        logger.warning(
            "[%s] Could not filter by source_url ($contains): %s. "
            "Attempting id-prefix deletion instead.",
            slug, exc,
        )
        try:
            # IDs are created as  f"{slug}_chunk_{i}"  by embedder.py
            all_ids = collection.get()["ids"]
            prefix_ids = [i for i in all_ids if i.startswith(f"{slug}_chunk_")]
            if prefix_ids:
                collection.delete(ids=prefix_ids)
                logger.info(
                    "[%s] Deleted %d stale chunk(s) by id-prefix.", slug, len(prefix_ids)
                )
                return len(prefix_ids)
        except Exception as exc2:
            logger.error("[%s] Fallback deletion also failed: %s", slug, exc2)
    return 0


def run_daily_update(urls: list[str] | None = None) -> dict:
    """
    Orchestrates the full daily refresh for the given URLs (default: all SCHEME_URLS).

    Steps per scheme:
      1. Scrape the Groww page via Playwright
      2. Chunk and classify the content
      3. Save updated processed JSON to data/processed/
      4. Delete stale ChromaDB entries for that scheme
      5. Embed and upsert fresh chunks into ChromaDB
      6. Update data/metadata.json

    Args:
        urls: List of Groww scheme URLs to refresh. If None, refreshes all SCHEME_URLS.

    Returns:
        summary dict: {
            "run_date": "YYYY-MM-DD",
            "schemes": {
                "<slug>": {"status": "ok", "chunks": N}  |
                           {"status": "error", "error": "..."}
            }
        }
    """
    urls = urls or SCHEME_URLS
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Use a single Playwright instance for all URLs (much faster than per-page launch)
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection("mutual_fund_facts")

    summary: dict = {
        "run_date": datetime.date.today().isoformat(),
        "schemes": {},
    }
    metadata: dict = (
        json.loads(METADATA_PATH.read_text(encoding="utf-8"))
        if METADATA_PATH.exists()
        else {}
    )

    logger.info(
        "=== Daily update started: %s (%d scheme(s)) ===",
        summary["run_date"], len(urls),
    )

    with sync_playwright() as pw:
        for url in urls:
            slug = _scheme_slug(url)
            logger.info("[%s] Scraping %s …", slug, url)

            try:
                # ── 1. Scrape ─────────────────────────────────────────────────
                scraped = scrape_scheme(url, playwright_instance=pw)

                # ── 2. Chunk ──────────────────────────────────────────────────
                chunks = chunk_document(
                    text=scraped["content"],
                    source_url=url,
                    scrape_date=scraped["scraped_at"],
                    scheme_name=scraped["scheme_name"],
                )

                # ── 3. Save processed JSON for audit ─────────────────────────
                processed_path = PROCESSED_DIR / f"{slug}.json"
                processed_path.write_text(
                    json.dumps(chunks, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

                # ── 4. Delete stale ChromaDB entries ─────────────────────────
                deleted = _delete_scheme_chunks(collection, slug)
                logger.info("[%s] Removed %d stale document(s).", slug, deleted)

                # ── 5. Embed + upsert fresh chunks ───────────────────────────
                ingest_chunks(chunks, id_prefix=slug)

                # ── 6. Update metadata ────────────────────────────────────────
                non_noise = [c for c in chunks if c.get("chunk_type") != "noise"]
                metadata[slug] = {
                    "source_url":   url,
                    "scrape_date":  scraped["scraped_at"],
                    "chunk_count":  len(non_noise),
                    "scheme_name":  scraped["scheme_name"],
                    "type":         "web",
                    "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
                    "fields_found": {
                        k: v for k, v in scraped.get("fields", {}).items() if v
                    },
                }
                summary["schemes"][slug] = {
                    "status": "ok",
                    "chunks": len(non_noise),
                }
                logger.info(
                    "[%s] \u2705  Done — %d non-noise chunks ingested.", slug, len(non_noise)
                )

            except Exception as exc:
                logger.error(
                    "[%s] \u274c  Failed: %s", slug, exc, exc_info=True
                )
                summary["schemes"][slug] = {
                    "status": "error",
                    "error": str(exc),
                }
                # Keep the existing metadata entry so the API still knows the
                # last known good scrape date — do NOT overwrite it.

    # ── Write metadata.json ───────────────────────────────────────────────────
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    ok_count = sum(1 for v in summary["schemes"].values() if v["status"] == "ok")
    err_count = len(summary["schemes"]) - ok_count
    logger.info(
        "=== Daily update complete: %d OK, %d errors ===",
        ok_count, err_count,
    )

    return summary
