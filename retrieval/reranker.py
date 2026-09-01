# retrieval/reranker.py
"""
Optional cross-encoder reranker for retrieval result refinement.

Phase 4 may activate this to improve precision when multiple chunks are
retrieved for the same query. Currently a pass-through stub.
"""


def rerank(query: str, chunks: list[dict]) -> list[dict]:
    """
    Re-order *chunks* by relevance to *query*.

    Args:
        query:  User's question.
        chunks: Candidate chunks returned by the retriever.

    Returns:
        Re-ranked list (currently returns input unchanged).
    """
    # TODO (Phase 4): integrate a cross-encoder model, e.g.
    #   cross-encoder/ms-marco-MiniLM-L-6-v2 via sentence-transformers
    return chunks
