import json
from pathlib import Path

# Check processed files
processed = list(Path("data/processed").glob("*.json"))
print(f"Processed files: {len(processed)}")
for f in processed:
    data = json.loads(f.read_text(encoding="utf-8"))
    print(f"  {f.name}: {len(data)} chunks")

# Check raw HTML
raw = list(Path("data/raw").glob("*.html"))
print(f"\nRaw HTML files: {len(raw)}")
for f in raw:
    print(f"  {f.name}: {f.stat().st_size:,} bytes")

# Check metadata
meta = json.loads(Path("data/metadata.json").read_text(encoding="utf-8"))
print(f"\nmetadata.json: {len(meta)} schemes")
for slug, m in meta.items():
    fields_found = len(m.get("fields_found", {}))
    print(f"  {slug}: {m['chunk_count']} chunks, {fields_found} fields, scraped {m['scrape_date']}")

# Check ChromaDB
import chromadb
client = chromadb.PersistentClient(path="vector_store/chroma_db")
col = client.get_collection("mutual_fund_facts")
print(f"\nChromaDB collection: {col.count()} total chunks")
