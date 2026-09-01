# ingest_all.py
"""
Full ingestion pipeline runner.

Run this once (and re-run when source data needs refreshing):
    python ingest_all.py

Steps:
  1. Scrape all 5 HDFC scheme pages from Groww (Playwright)
  2. Clean & chunk each page's text
  3. Embed chunks and upsert into ChromaDB
  4. Update data/metadata.json
"""
import json
from pathlib import Path

from ingestion.scraper  import scrape_all
from ingestion.chunker  import chunk_document
from ingestion.embedder import ingest_chunks

PROCESSED_DIR = Path("data/processed")
METADATA_FILE  = Path("data/metadata.json")


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    metadata = {}

    print("=" * 60)
    print("HDFC Mutual Fund RAG — Ingestion Pipeline")
    print("=" * 60)

    scraped_items = scrape_all()

    if not scraped_items:
        print("\n[ingest_all] ✗ No pages scraped successfully. Aborting.")
        return

    print(f"\n[ingest_all] Processing {len(scraped_items)} scraped page(s)...\n")

    for item in scraped_items:
        slug        = item["slug"]
        url         = item["url"]
        date        = item["scraped_at"]
        scheme_name = item.get("scheme_name", slug.replace("-", " ").title())

        print(f"[ingest_all] -- {scheme_name} ({slug})")

        # ── 1. Chunk ──────────────────────────────────────────────────────────
        chunks = chunk_document(
            text=item["content"],
            source_url=url,
            scrape_date=date,
            scheme_name=scheme_name,
        )
        print(f"[ingest_all]    {len(chunks)} chunks generated")

        # ── 2. Save processed chunks as JSON ─────────────────────────────────
        processed_path = PROCESSED_DIR / f"{slug}.json"
        processed_path.write_text(
            json.dumps(chunks, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[ingest_all]    Saved → {processed_path}")

        # ── 3. Embed & upsert in ChromaDB ─────────────────────────────────────
        ingest_chunks(chunks, id_prefix=slug)

        # ── 4. Record metadata ────────────────────────────────────────────────
        metadata[slug] = {
            "source_url":   url,
            "scrape_date":  date,
            "chunk_count":  len(chunks),
            "scheme_name":  scheme_name,
            "type":         "web",
            "fields_found": {k: v for k, v in item.get("fields", {}).items() if v},
        }
        print()

    # ── Write metadata.json ───────────────────────────────────────────────────
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    METADATA_FILE.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=" * 60)
    print(f"[ingest_all] [OK] metadata.json updated ({len(metadata)} schemes)")
    print(f"[ingest_all] [OK] ChromaDB upserted")
    print(f"[ingest_all] [OK] Ingestion complete.")
    print("=" * 60)

    # ── Summary table ─────────────────────────────────────────────────────────
    print("\nSummary:")
    print(f"  {'Scheme':<50} {'Chunks':>6}  {'Fields Found':>12}")
    print(f"  {'-'*50} {'-'*6}  {'-'*12}")
    for slug, m in metadata.items():
        fields_found = len(m.get("fields_found", {}))
        print(f"  {m['scheme_name']:<50} {m['chunk_count']:>6}  {fields_found:>12}")


if __name__ == "__main__":
    main()
