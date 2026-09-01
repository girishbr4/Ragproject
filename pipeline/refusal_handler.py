# pipeline/refusal_handler.py
"""
Generates canned refusal messages for advisory and PII queries.

Returns a string — no LLM call is made, keeping refusals free and instant.
"""

REFUSAL_TEMPLATE = (
    "I'm designed to answer only factual questions about HDFC mutual fund "
    "schemes (e.g., expense ratios, exit loads, SIP amounts, lock-in periods).\n\n"
    "I'm unable to provide investment advice, recommendations, or performance comparisons.\n"
    "For investor education, please visit: https://www.amfiindia.com/investor-corner\n\n"
    "> Facts-only. No investment advice."
)

PII_TEMPLATE = (
    "For your privacy and security, I cannot process queries that contain "
    "personal identifiers such as PAN, Aadhaar, account numbers, or contact details.\n"
    "Please rephrase your question without personal information.\n\n"
    "> Facts-only. No investment advice."
)


def get_refusal(reason: str) -> str:
    """
    Return the appropriate canned refusal message.

    Args:
        reason: "pii" for personal-data queries, anything else for advisory.

    Returns:
        Plain-text refusal string including the mandatory disclaimer.
    """
    return PII_TEMPLATE if reason == "pii" else REFUSAL_TEMPLATE
