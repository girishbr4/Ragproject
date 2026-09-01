# pipeline/response_formatter.py
"""
Post-processes raw LLM output to enforce:
  - Maximum 3 sentences
  - Mandatory source citation
  - Mandatory date footer
  - Permanent facts-only disclaimer
"""
import re


def format_response(raw: str, source_url: str, date: str) -> str:
    """
    Clean and standardise a raw LLM response string.

    Steps:
      1. Strip leading/trailing whitespace.
      2. Split into sentences and trim to at most 3.
      3. Inject "Source: <url>" if the LLM omitted it.
      4. Inject "Last updated from sources: <date>" if omitted.
      5. Append the mandatory facts-only disclaimer.

    Args:
        raw:        Raw text returned by the LLM.
        source_url: Citation URL (from the top retrieved chunk).
        date:       Scrape/update date string (from the top retrieved chunk).

    Returns:
        Formatted, compliant response string.
    """
    text = raw.strip()

    # ── 0. Normalise Unicode spaces inserted by GPT-class models ─────────────
    # Models like gpt-oss-120b use narrow no-break space (U+202F) in numbers
    # e.g. "NIFTY\u202f100" — normalise to regular ASCII space.
    text = text.replace('\u202f', ' ').replace('\u00a0', ' ')

    # ── 1. Trim to max 3 sentences ────────────────────────────────────────────
    # Split on sentence-ending punctuation followed by whitespace or newline.
    # Keeps the punctuation attached to the sentence.
    sentence_re = re.compile(r"(?<=[.?!])\s+")
    sentences   = sentence_re.split(text)
    trimmed     = " ".join(sentences[:3]).strip()

    # ── 2. Ensure source citation ─────────────────────────────────────────────
    if "Source:" not in trimmed:
        trimmed += f"\nSource: {source_url}"

    # ── 3. Ensure date footer ─────────────────────────────────────────────────
    if "Last updated" not in trimmed:
        trimmed += f"\nLast updated from sources: {date}"

    # ── 4. Mandatory disclaimer ───────────────────────────────────────────────
    trimmed += "\n\n> Facts-only. No investment advice."

    return trimmed
