"""
inspect_embeddings.py
─────────────────────
Inspect the ChromaDB vector store and show embedding examples.

Run from project root:
    python scripts/inspect_embeddings.py
"""
import sys
import io
from pathlib import Path
from collections import Counter

# Force UTF-8 output on Windows to avoid cp1252 errors
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from sentence_transformers import SentenceTransformer
from config import CHROMA_DB_PATH, EMBEDDING_MODEL, TOP_K

# ── Helpers ───────────────────────────────────────────────────────────────────
def divider(title="", width=68):
    if title:
        pad = (width - len(title) - 2) // 2
        print(f"\n{'=' * pad} {title} {'=' * (width - pad - len(title) - 2)}")
    else:
        print("=" * width)

def bar(n, scale=2):
    return "#" * max(1, n // scale)

CHUNK_TYPE_LABEL = {
    "structured_facts": "[FACTS]",
    "faq_text":         "[FAQ  ]",
    "fund_description": "[DESC ]",
    "holdings":         "[HOLD ]",
    "noise":            "[NOISE]",
}

# ── 1. Connect to ChromaDB ────────────────────────────────────────────────────
print("\nLoading model and connecting to ChromaDB...")
client     = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_collection("mutual_fund_facts")
model      = SentenceTransformer(EMBEDDING_MODEL)

# Fetch all documents
all_data      = collection.get(include=["metadatas", "embeddings", "documents"])
all_docs      = all_data["documents"]
all_metas     = all_data["metadatas"]
all_embeddings = np.array(all_data["embeddings"])

total   = len(all_docs)
emb_dim = all_embeddings.shape[1] if total > 0 else 0

divider("CHROMADB COLLECTION OVERVIEW")
print(f"  Collection name  : mutual_fund_facts")
print(f"  Total chunks     : {total}")
print(f"  Embedding model  : {EMBEDDING_MODEL}")
print(f"  Embedding dim    : {emb_dim}")
print(f"  Embedding dtype  : {all_embeddings.dtype}")
print(f"  Matrix shape     : {all_embeddings.shape}")

# ── 2. Breakdown by chunk_type and scheme ─────────────────────────────────────
divider("CHUNK TYPE BREAKDOWN")
type_counts   = Counter(m.get("chunk_type", "unknown") for m in all_metas)
scheme_counts = Counter(m.get("scheme_name", "unknown") for m in all_metas)

print(f"\n  {'Chunk Type':<22} {'Count':>6}  Bar")
print(f"  {'-'*22} {'-'*6}  {'-'*30}")
for ct, count in sorted(type_counts.items(), key=lambda x: -x[1]):
    label = CHUNK_TYPE_LABEL.get(ct, f"[{ct[:5]}]")
    print(f"  {label} {ct:<15} {count:>6}  {bar(count)}")

print(f"\n  {'Scheme':<45} {'Chunks':>6}")
print(f"  {'-'*45} {'-'*6}")
for scheme, count in sorted(scheme_counts.items(), key=lambda x: -x[1]):
    short = (scheme.replace("HDFC ", "")
                   .replace(" Direct Growth", "")
                   .replace(" Direct Plan Growth", ""))
    print(f"  {short:<45} {count:>6}")

# ── 3. Sample embedding vectors ───────────────────────────────────────────────
divider("SAMPLE EMBEDDING VECTORS (first 3 chunks)")

for i in range(min(3, total)):
    ct   = all_metas[i].get("chunk_type", "?")
    emb  = all_embeddings[i]
    norm = np.linalg.norm(emb)
    label = CHUNK_TYPE_LABEL.get(ct, ct)
    preview = all_docs[i][:100].replace("\n", " ")

    print(f"\n  [{i}] {label}  {all_metas[i].get('scheme_name','').replace('HDFC ','')}")
    print(f"       Text    : {preview}...")
    print(f"       Shape   : ({emb_dim},)   Norm: {norm:.6f}")
    print(f"       Values  : [{', '.join(f'{v:.5f}' for v in emb[:10])} ...]")
    print(f"       Min/Max : {emb.min():.5f} / {emb.max():.5f}   Std: {emb.std():.5f}")

# ── 4. Cosine similarity matrix between structured_facts chunks ───────────────
divider("COSINE SIMILARITY - structured_facts chunks (across schemes)")

sf_indices    = [i for i, m in enumerate(all_metas) if m.get("chunk_type") == "structured_facts"]
sf_embeddings = all_embeddings[sf_indices]
sf_labels     = [
    all_metas[i].get("scheme_name", "?")
        .replace("HDFC ", "")
        .replace(" Fund Direct Growth", "")
        .replace(" Fund Direct Plan Growth", "")
    for i in sf_indices
]

# Deduplicate labels (take first occurrence per scheme)
seen_labels, unique_idx = [], []
for j, lbl in enumerate(sf_labels):
    if lbl not in seen_labels:
        seen_labels.append(lbl)
        unique_idx.append(j)

uf_emb    = sf_embeddings[unique_idx]
uf_labels = seen_labels
sim_matrix = uf_emb @ uf_emb.T  # cosine (vectors are normalized)

COL_W = 14
print(f"\n  {'':28}" + "".join(f"{l[:COL_W-1]:>{COL_W}}" for l in uf_labels))
print(f"  {'-'*28}" + f"{'-'*COL_W}" * len(uf_labels))
for i, label_i in enumerate(uf_labels):
    row = f"  {label_i[:28]:<28}"
    for j in range(len(uf_labels)):
        sim = sim_matrix[i][j]
        flag = " <---" if i != j and sim > 0.85 else ""
        row += f"{sim:>{COL_W}.4f}"
    print(row)

print(f"\n  Note: diagonal = 1.000 (self-similarity)")
print(f"  High off-diagonal similarity = overlapping content between schemes")
print(f"  Low similarity = well-separated factual blocks (ideal for retrieval)")

# ── 5. Live retrieval examples ────────────────────────────────────────────────
divider("LIVE RETRIEVAL EXAMPLES")

BGE_PREFIX = "Represent this sentence for searching relevant passages: "
THRESHOLD  = 0.35

TEST_QUERIES = [
    ("expense ratio",    "What is the expense ratio of HDFC Mid Cap Fund?"),
    ("lock-in period",   "What is the lock-in period for HDFC ELSS Tax Saver Fund?"),
    ("minimum SIP",      "What is the minimum SIP amount for HDFC Small Cap Fund?"),
    ("benchmark index",  "What is the benchmark index of HDFC Large Cap Fund?"),
    ("riskometer",       "What is the riskometer level of HDFC Gold ETF Fund of Fund?"),
]

for topic, query in TEST_QUERIES:
    print(f"\n  Query [{topic}]")
    print(f"  Q: {query}")
    print(f"  {'-'*64}")

    qvec = model.encode(BGE_PREFIX + query, normalize_embeddings=True)
    results = collection.query(
        query_embeddings=[qvec.tolist()],
        n_results=TOP_K,
        include=["documents", "metadatas", "distances"],
    )
    docs  = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    shown = 0
    for doc, meta, dist in zip(docs, metas, dists):
        sim    = 1 - dist
        ct     = meta.get("chunk_type", "?")
        label  = CHUNK_TYPE_LABEL.get(ct, ct)
        scheme = (meta.get("scheme_name", "?")
                      .replace("HDFC ", "")
                      .replace(" Direct Growth", "")
                      .replace(" Direct Plan Growth", ""))
        preview = doc[:200].replace("\n", " | ")

        print(f"\n  Result #{shown+1}  sim={sim:.4f}  {label}  [{scheme}]")
        print(f"  {preview}")
        shown += 1
        if shown >= 2:
            break

    if shown == 0:
        print(f"  [NO RESULTS above threshold {THRESHOLD}]")

divider()
print(f"\n  Done. {total} chunks | {emb_dim}-dim BGE embeddings | {len(type_counts)} chunk types\n")
