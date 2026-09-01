# pipeline/main.py
"""
RAG Pipeline Orchestrator.

Full flow for every user query:

  classify(query)
    ├── "pii"      → get_refusal("pii")              [hard block]
    ├── "advisory" → get_refusal("advisory")          [polite refusal]
    └── "factual"
          → retrieve(query)
              ├── [] (empty) → _FALLBACK              [nothing found]
              └── [chunks]
                    → _check_hdfc_scope(query)        [non-HDFC guard]
                    → build_prompt(query, chunks)
                    → call_llm(prompt)
                    → format_response(raw, url, date)
"""
from pipeline.classifier        import classify
from retrieval.retriever         import retrieve, SCHEME_KEYWORD_MAP
from pipeline.prompt_builder     import build_prompt
from pipeline.llm_client         import call_llm
from pipeline.response_formatter import format_response
from pipeline.refusal_handler    import get_refusal

_FALLBACK = (
    "I could not find this information in the official sources. "
    "Please visit https://www.amfiindia.com for more details.\n\n"
    "> Facts-only. No investment advice."
)

_NON_HDFC_RESPONSE = (
    "This assistant covers only HDFC Mutual Fund schemes. "
    "For other fund houses, please visit https://www.amfiindia.com.\n\n"
    "> Facts-only. No investment advice."
)

# Non-HDFC AMC names that should trigger the scope guard
_OTHER_AMC_KEYWORDS = frozenset([
    "sbi", "icici", "axis", "kotak", "mirae", "nippon", "dsp",
    "franklin", "tata", "uti", "aditya birla", "bandhan", "parag parikh",
    "quant", "motilal", "canara", "baroda", "whiteoak", "zerodha",
    "groww fund", "hdfc bank",   # groww AMC is separate from HDFC MF
])

# HDFC-specific keywords — if present, never trigger non-HDFC guard
_HDFC_KEYWORDS = frozenset([
    "hdfc", "hdfc fund", "hdfc mutual",
    *SCHEME_KEYWORD_MAP.keys(),
])


def _is_non_hdfc_query(query: str) -> bool:
    """
    Return True if the query clearly asks about a non-HDFC fund house
    and does not mention any HDFC scheme.
    """
    q = query.lower()
    mentions_hdfc  = any(kw in q for kw in _HDFC_KEYWORDS)
    mentions_other = any(kw in q for kw in _OTHER_AMC_KEYWORDS)
    return mentions_other and not mentions_hdfc


def answer(query: str) -> str:
    """
    Full RAG pipeline: classify → scope-guard → retrieve → generate → format.

    Args:
        query: User's natural-language question.

    Returns:
        A formatted, compliant response string ready for display.
    """
    # ── 1. Classify intent ────────────────────────────────────────────────────
    intent = classify(query)
    if intent in ("advisory", "pii"):
        return get_refusal(intent)

    # ── 2. Non-HDFC scope guard ───────────────────────────────────────────────
    if _is_non_hdfc_query(query):
        return _NON_HDFC_RESPONSE

    # ── 3. Multi-pass retrieval ───────────────────────────────────────────────
    chunks = retrieve(query)
    if not chunks:
        return _FALLBACK

    # ── 4. Build prompt → LLM → format ────────────────────────────────────────────
    prompt = build_prompt(query, chunks)
    raw    = call_llm(prompt)

    # Guard: LLM returned empty string (refused to answer, overloaded, etc.)
    if not raw or not raw.strip():
        return _FALLBACK

    return format_response(raw, chunks[0]["source_url"], chunks[0]["date"])
