# pipeline/classifier.py
"""
Two-tier query classifier.

Tier 1 — Regex keyword matching (fast, zero cost, zero latency).
Tier 2 — LLM zero-shot classification via Groq (for ambiguous queries
          that pass Tier 1 but may still be non-factual).

Returns one of: "advisory" | "pii" | "factual"
"""
import re

# ── Tier-1 Pattern Lists ──────────────────────────────────────────────────────
ADVISORY_PATTERNS: list[str] = [
    r"\bshould i\b",
    r"\bshould i invest\b",
    r"\bwhich fund\b",
    r"\bwhich is better\b",
    r"\bbetter\b",
    r"\brecommend\b",
    r"\brecommendation\b",
    r"\binvest in\b",
    r"\bperformance\b",
    r"\breturns\b",
    r"\bbest fund\b",
    r"\bworst fund\b",
    r"\bcompare\b",
    r"\boutperform\b",
    r"\bprediction\b",
    r"\bforecast\b",
    r"\bwill it go up\b",
    r"\bshould i buy\b",
    r"\bshould i sell\b",
    r"\bgood investment\b",
    r"\bworth investing\b",
]

PII_PATTERNS: list[str] = [
    r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",   # PAN card
    r"\b\d{12}\b",                    # Aadhaar number
    r"\b\d{10}\b",                    # Phone number
]

_ADVISORY_RE = re.compile("|".join(ADVISORY_PATTERNS), re.IGNORECASE)
_PII_RE      = re.compile("|".join(PII_PATTERNS))

# ── Ambiguity signals: trigger Tier-2 LLM check ──────────────────────────────
# These words may appear in legitimate factual queries OR advisory ones.
# Tier-2 resolves the ambiguity by asking the LLM to classify.
_AMBIGUOUS_PATTERNS: list[str] = [
    r"\bgood\b",
    r"\bworth\b",
    r"\bsafe\b",
    r"\brisky\b",
    r"\bsuitable\b",
    r"\badvise\b",
    r"\badvice\b",
    r"\bopinion\b",
]
_AMBIGUOUS_RE = re.compile("|".join(_AMBIGUOUS_PATTERNS), re.IGNORECASE)

# ── Tier-2 LLM classification prompt ─────────────────────────────────────────
_TIER2_SYSTEM = (
    "You are a query classifier for a facts-only mutual fund FAQ bot. "
    "Classify the user's query into exactly one of these categories:\n"
    "  advisory — requests investment advice, recommendations, opinions, "
    "predictions, or performance comparisons\n"
    "  factual  — asks for a specific factual detail (expense ratio, exit load, "
    "SIP amount, lock-in period, benchmark, fund manager, riskometer, NAV, AUM)\n\n"
    "Respond with exactly one word: advisory OR factual. No explanation."
)


def _tier2_classify(query: str) -> str:
    """
    LLM zero-shot classification for ambiguous queries.

    Only called when Tier-1 did not definitively classify the query.
    Uses a tiny prompt with temperature=0 for deterministic output.

    Returns "advisory" or "factual". Falls back to "factual" on any error.
    """
    try:
        # Import here to avoid circular dependency and cold-start cost
        from pipeline.llm_client import call_llm_raw
        response = call_llm_raw(
            system_prompt=_TIER2_SYSTEM,
            user_message=query,
            max_tokens=5,
        ).strip().lower()
        if "advisory" in response:
            return "advisory"
    except Exception:
        pass   # fail open — treat as factual, better than refusing valid queries
    return "factual"


def classify(query: str) -> str:
    """
    Classify *query* into one of three intent categories.

    Flow:
      1. PII check (regex) → "pii"
      2. Advisory check (regex) → "advisory"
      3. Ambiguity check (regex) → Tier-2 LLM → "advisory" or "factual"
      4. Default → "factual"

    Args:
        query: Raw user input string.

    Returns:
        "pii"      — query contains personal identifiers → hard block.
        "advisory" — query requests investment advice → polite refusal.
        "factual"  — query is a legitimate factual question → proceed to RAG.
    """
    if _PII_RE.search(query):
        return "pii"
    if _ADVISORY_RE.search(query):
        return "advisory"
    if _AMBIGUOUS_RE.search(query):
        return _tier2_classify(query)
    return "factual"
