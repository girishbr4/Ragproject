"""
Phase 3 runner: embed existing processed chunks into ChromaDB.

Loads data/processed/*.json (already chunked by ingest_all.py / chunker.py)
and upserts them into ChromaDB using BAAI/bge-small-en-v1.5.

Run from project root:
    python scripts/run_phase3.py
"""
import json
import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.embedder import ingest_chunks
from ingestion.chunker import classify_chunk_type
from config import EMBEDDING_MODEL

PROCESSED_DIR = Path("data/processed")


def backfill_chunk_type(chunks: list[dict]) -> list[dict]:
    """
    Add chunk_type to chunks that were saved before the tagging was added.
    The header chunk (index 0) is always structured_facts.
    """
    result = []
    for i, c in enumerate(chunks):
        c = dict(c)
        if "chunk_type" not in c:
            if i == 0:
                c["chunk_type"] = "structured_facts"
            else:
                c["chunk_type"] = classify_chunk_type(c["text"])
        result.append(c)
    return result


def main():
    json_files = sorted(PROCESSED_DIR.glob("*.json"))
    json_files = [f for f in json_files if f.name != ".gitkeep"]

    if not json_files:
        print(f"[phase3] No JSON files found in {PROCESSED_DIR}. Run ingest_all.py first.")
        sys.exit(1)

    print("=" * 60)
    print(f"Phase 3 — Embedding & Vector Store")
    print(f"Model: {EMBEDDING_MODEL}")
    print(f"Files: {len(json_files)} scheme(s)")
    print("=" * 60)

    total_clean = 0
    total_noise = 0

    for json_path in json_files:
        slug = json_path.stem
        print(f"\n[phase3] Processing: {slug}")

        chunks = json.loads(json_path.read_text(encoding="utf-8"))
        chunks = backfill_chunk_type(chunks)

        noise_count = sum(1 for c in chunks if c.get("chunk_type") == "noise")
        clean_count = len(chunks) - noise_count
        total_clean += clean_count
        total_noise += noise_count

        print(f"[phase3]   Total chunks: {len(chunks)} | Clean: {clean_count} | Noise (skipped): {noise_count}")

        ingest_chunks(chunks, id_prefix=slug)

    print("\n" + "=" * 60)
    print(f"[phase3] Done.")
    print(f"[phase3]   Embedded: {total_clean} chunks")
    print(f"[phase3]   Skipped:  {total_noise} noise chunks")
    print("=" * 60)

    # Quick verification
    print("\n[phase3] Running verification query...")
    from retrieval.retriever import retrieve
    test_chunks = retrieve("What is the expense ratio of HDFC Mid Cap Fund?")
    if test_chunks:
        print(f"[phase3] Verification passed -- {len(test_chunks)} chunk(s) returned")
        print(f"         Top chunk type: {test_chunks[0].get('chunk_type', 'unknown')}")
        print(f"         Scheme: {test_chunks[0].get('scheme_name', 'unknown')}")
        print(f"         Preview: {test_chunks[0]['text'][:120]}...")
    else:
        print("[phase3] Verification returned 0 chunks -- check SIMILARITY_THRESHOLD in config.py")


if __name__ == "__main__":
    main()
