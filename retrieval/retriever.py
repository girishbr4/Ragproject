# retrieval/retriever.py
"""
Multi-pass retrieval engine using ChromaDB + BAAI/bge-small-en-v1.5.

Strategy (based on analysis of data/processed/ chunk structure):

  Pass 1 — PRIORITY: always fetch structured_facts chunks first.
            These are the key-facts blocks (expense ratio, SIP, risk,
            benchmark, fund manager, lock-in) stored at index 0-2 of
            each scheme file. Scoped to detected scheme if identifiable.

  Pass 2 — SEMANTIC: cosine-similarity search over faq_text +
            fund_description chunks, scoped to detected scheme.

  Pass 3 — HOLDINGS (conditional): only when query mentions holdings/
            portfolio/stock/sector. Fetches top-2 holdings chunks.

  Noise chunks are never embedded so never returned.

BGE asymmetric encoding:
  - Index time (embedder.py): passages encoded as-is, no prefix
  - Query time (this file): queries prefixed with _BGE_QUERY_PREFIX
"""
import chromadb
from sentence_transformers import SentenceTransformer
from config import CHROMA_DB_PATH, EMBEDDING_MODEL, TOP_K, SIMILARITY_THRESHOLD

_client     = chromadb.PersistentClient(path=CHROMA_DB_PATH)
_collection = _client.get_collection("mutual_fund_facts")
_model      = SentenceTransformer(EMBEDDING_MODEL)

# BGE query prefix — applied at retrieval time only (not at index time)
_BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

# Map query keywords → exact ChromaDB scheme_name metadata values
SCHEME_KEYWORD_MAP: dict[str, str] = {
    "mid cap":   "HDFC Mid Cap Fund Direct Growth",
    "midcap":    "HDFC Mid Cap Fund Direct Growth",
    "mid-cap":   "HDFC Mid Cap Fund Direct Growth",
    "small cap": "HDFC Small Cap Fund Direct Growth",
    "smallcap":  "HDFC Small Cap Fund Direct Growth",
    "small-cap": "HDFC Small Cap Fund Direct Growth",
    "large cap": "HDFC Large Cap Fund Direct Growth",
    "largecap":  "HDFC Large Cap Fund Direct Growth",
    "large-cap": "HDFC Large Cap Fund Direct Growth",
    "gold":      "HDFC Gold ETF Fund of Fund Direct Plan Growth",
    "elss":      "HDFC ELSS Tax Saver Fund Direct Plan Growth",
    "tax saver": "HDFC ELSS Tax Saver Fund Direct Plan Growth",
    "tax-saver": "HDFC ELSS Tax Saver Fund Direct Plan Growth",
}

# Keywords that signal a portfolio/holdings question
_HOLDINGS_KEYWORDS = frozenset([
    "holding", "holdings", "portfolio", "stock", "stocks",
    "sector", "allocation", "invest", "top holding",
])


def _detect_scheme(query: str) -> str | None:
    """
    Return the exact ChromaDB scheme_name if the query mentions a specific
    HDFC scheme. Returns None for generic or unrecognised queries.
    """
    q = query.lower()
    for keyword, scheme_name in SCHEME_KEYWORD_MAP.items():
        if keyword in q:
            return scheme_name
    return None


def _is_holdings_query(query: str) -> bool:
    """True when the query is about fund portfolio/holdings composition."""
    q = query.lower()
    return any(kw in q for kw in _HOLDINGS_KEYWORDS)


def _build_where(chunk_type_filter: dict, scheme: str | None) -> dict:
    """
    Compose a ChromaDB $and where-filter combining chunk_type and,
    optionally, scheme_name.
    """
    if scheme:
        return {
            "$and": [
                chunk_type_filter,
                {"scheme_name": {"$eq": scheme}},
            ]
        }
    return chunk_type_filter


def _query_pass(
    query_embedding: list[float],
    where: dict,
    n: int,
) -> list[dict]:
    """
    Execute one ChromaDB query pass and return chunks above the
    similarity threshold as a list of dicts.
    """
    try:
        results = _collection.query(
            query_embeddings=[query_embedding],
            n_results=n,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        # e.g. where-filter matches 0 documents — ChromaDB raises
        return []

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        if dist < (1 - SIMILARITY_THRESHOLD):
            chunks.append({
                "text":        doc,
                "source_url":  meta["source_url"],
                "date":        meta["date"],
                "scheme_name": meta.get("scheme_name", ""),
                "chunk_type":  meta.get("chunk_type", ""),
            })
    return chunks


def retrieve(query: str) -> list[dict]:
    """
    Multi-pass retrieval — returns merged, de-duplicated chunks ordered by
    priority (structured_facts first, then semantic, then holdings).

    Args:
        query: User's natural-language question.

    Returns:
        List of chunk dicts: {text, source_url, date, scheme_name, chunk_type}.
        Empty list if nothing meets SIMILARITY_THRESHOLD → triggers fallback.
    """
    prefixed_query  = _BGE_QUERY_PREFIX + query
    query_embedding = _model.encode(
        prefixed_query,
        normalize_embeddings=True,
    ).tolist()

    detected_scheme = _detect_scheme(query)

    # ── Pass 1: structured_facts (always retrieved, scheme-scoped) ───────────
    priority_chunks = _query_pass(
        query_embedding,
        where=_build_where(
            {"chunk_type": {"$eq": "structured_facts"}},
            detected_scheme,
        ),
        n=TOP_K,
    )

    # ── Pass 2: faq_text + fund_description (semantic, scheme-scoped) ────────
    semantic_chunks = _query_pass(
        query_embedding,
        where=_build_where(
            {"chunk_type": {"$in": ["faq_text", "fund_description"]}},
            detected_scheme,
        ),
        n=TOP_K,
    )

    # ── Pass 3: holdings (only for portfolio queries) ─────────────────────────
    holdings_chunks: list[dict] = []
    if _is_holdings_query(query):
        holdings_chunks = _query_pass(
            query_embedding,
            where=_build_where(
                {"chunk_type": {"$eq": "holdings"}},
                detected_scheme,
            ),
            n=2,
        )

    # ── Merge with de-duplication ─────────────────────────────────────────────
    seen:   set[str]  = set()
    merged: list[dict] = []
    for chunk in priority_chunks + semantic_chunks + holdings_chunks:
        if chunk["text"] not in seen:
            seen.add(chunk["text"])
            merged.append(chunk)

    return merged
