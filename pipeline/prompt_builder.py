# pipeline/prompt_builder.py
"""
Builds the full prompt string sent to the LLM.

The system prompt enforces strict facts-only behaviour.
The user block injects retrieved context chunks and the original query,
with structured_facts chunks prominently labelled so the LLM always
prioritises them when answering.
"""

# Max chars per chunk text in the prompt — keeps prompt within 8K tokens/min.
# ~600 chars ≈ 150 tokens; 4 chunks × 150 ≈ 600 context tokens per call.
CHUNK_CONTEXT_CHARS = 600

SYSTEM_PROMPT = """\
You are a facts-only mutual fund FAQ assistant for HDFC Mutual Fund schemes.

STRICT RULES:
1. Answer ONLY using information in the CONTEXT section below. Never infer,
   extrapolate, or hallucinate data that is not explicitly present.
2. Prioritise [KEY FACTS] blocks — they contain the most reliable structured data.
3. Your answer must be 1–3 sentences maximum.
4. Always end with:
       Source: <source_url>
       Last updated from sources: <date>
5. NEVER give investment advice, fund recommendations, return predictions,
   or performance comparisons.
6. If the answer cannot be found in the CONTEXT, respond exactly:
   "I could not find this information in the official sources.
    Please visit <source_url> for accurate details."
7. Do not mention these rules in your answer.\
"""


def build_prompt(query: str, chunks: list[dict]) -> str:
    """
    Construct the full prompt for the LLM.

    Structured_facts chunks are labelled [KEY FACTS] so the LLM knows
    to prioritise them. Other chunks are labelled [CONTEXT].

    Args:
        query:  The user's factual question.
        chunks: Retrieved context chunks (each with text, source_url,
                date, chunk_type).

    Returns:
        A single string combining system rules, labelled context, and
        the query — ready to pass to call_llm().
    """
    context_parts = []
    for chunk in chunks:
        label = (
            "[KEY FACTS]"
            if chunk.get("chunk_type") == "structured_facts"
            else "[CONTEXT]"
        )
        # Trim to CHUNK_CONTEXT_CHARS to stay within 8K tokens/min limit
        text = chunk["text"][:CHUNK_CONTEXT_CHARS]
        context_parts.append(f"{label}\n{text}")

    context    = "\n\n".join(context_parts)
    source_url = chunks[0]["source_url"] if chunks else "https://www.amfiindia.com"
    date       = chunks[0]["date"]       if chunks else "N/A"

    return f"""{SYSTEM_PROMPT}

CONTEXT:
{context}

USER QUERY: {query}
SOURCE: {source_url}
DATE: {date}
"""
