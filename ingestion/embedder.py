# ingestion/embedder.py
"""
Embedding and ChromaDB ingestion module.

Model: BAAI/bge-small-en-v1.5
  - Significantly outperforms all-MiniLM-L6-v2 on MTEB retrieval benchmarks
  - Supports BGE-style query prefix: queries are prefixed with
    "Represent this sentence for searching relevant passages: "
    at retrieval time (handled in retriever.py)
  - 384-dim embeddings, ~33 MB on disk, ~2x faster MTEB retrieval score

Noise filtering:
  Chunks tagged chunk_type == "noise" by chunker.py are skipped entirely
  before encoding. This reduces ChromaDB collection size by ~55% and
  keeps irrelevant Groww nav/footer content out of similarity search.

chunk_type metadata:
  Each embedded chunk stores its chunk_type in ChromaDB metadata so
  the retriever can use $in / $eq where-filters for multi-pass retrieval
  (structured_facts → faq_text/fund_description → holdings).
"""
import chromadb
from sentence_transformers import SentenceTransformer
from config import CHROMA_DB_PATH, EMBEDDING_MODEL

_client     = chromadb.PersistentClient(path=CHROMA_DB_PATH)
_collection = _client.get_or_create_collection("mutual_fund_facts")
_model      = SentenceTransformer(EMBEDDING_MODEL)

# Noise chunk types are excluded from embedding entirely
_NOISE_TYPES = {"noise"}


def ingest_chunks(chunks: list[dict], id_prefix: str = "chunk") -> None:
    """
    Embed and store non-noise chunks in ChromaDB.

    Chunks with chunk_type == "noise" are silently skipped — they are
    written to data/processed/ for audit purposes but must never enter
    the vector store.

    Args:
        chunks:    List of dicts with keys: text, source_url, date,
                   scheme_name, chunk_type.
        id_prefix: Scheme slug used to build unique chunk IDs (avoids
                   collisions on re-ingest runs for different schemes).
    """
    if not chunks:
        return

    # ── Filter noise before encoding ─────────────────────────────────────────
    clean_chunks = [
        c for c in chunks
        if c.get("chunk_type", "faq_text") not in _NOISE_TYPES
    ]
    skipped = len(chunks) - len(clean_chunks)
    if skipped:
        print(f"[embedder]   Skipped {skipped} noise chunk(s)")

    if not clean_chunks:
        print("[embedder]   No non-noise chunks to embed — skipping.")
        return

    texts = [c["text"] for c in clean_chunks]

    # ── Encode with bge-small-en-v1.5 ────────────────────────────────────────
    # BGE models expect a task prefix only at *query* time, not at index time.
    # At index time we encode the passage text as-is.
    embeddings = _model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,   # cosine similarity via dot product
    ).tolist()

    ids = [f"{id_prefix}_chunk_{i}" for i in range(len(clean_chunks))]
    metadatas = [
        {
            "source_url":  c["source_url"],
            "date":        c["date"],
            "scheme_name": c.get("scheme_name", ""),
            "chunk_type":  c.get("chunk_type", "faq_text"),  # for where-filters
        }
        for c in clean_chunks
    ]

    _collection.upsert(
        documents=texts,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas,
    )
    print(
        f"[embedder]   Upserted {len(clean_chunks)} chunks "
        f"(prefix={id_prefix!r}, model={EMBEDDING_MODEL!r})"
    )


def get_collection():
    """Return the ChromaDB collection (used by retriever.py)."""
    return _collection
