# pipeline/llm_client.py
"""
LLM client — Groq API with openai/gpt-oss-120b.

Rate limits (free tier):
  30 RPM | 1K req/day | 8K tokens/min | 200K tokens/day

Three mitigations implemented:

1. Response cache (LRU, LLM_CACHE_SIZE slots)
   Identical query strings return the cached answer instantly —
   zero tokens, zero requests consumed.

2. Retry with exponential backoff (LLM_MAX_RETRIES attempts)
   On 429 RateLimitError: sleep 2 s → 4 s → 8 s then raise.
   On 503 ServiceUnavailable: same backoff.

3. Token budget discipline
   - max_tokens = LLM_MAX_TOKENS (200) — 3 sentences needs ~100 tokens
   - Prompt context is trimmed in build_prompt() to TOP_K chunks;
     each chunk is capped at CHUNK_CONTEXT_CHARS chars before sending.
"""
import os
import time
import logging
import hashlib
from functools import lru_cache

from groq import Groq, RateLimitError
from config import (
    LLM_MODEL,
    LLM_MAX_TOKENS,
    LLM_MAX_RETRIES,
    LLM_RETRY_BASE_DELAY,
    LLM_CACHE_SIZE,
)
from pipeline.prompt_builder import CHUNK_CONTEXT_CHARS

logger  = logging.getLogger(__name__)
_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))


def _call_with_retry(messages: list[dict]) -> str:
    """
    Send messages to Groq and return response text.
    Retries up to LLM_MAX_RETRIES times on 429 / 503 with exponential backoff.

    Args:
        messages: List of Groq chat message dicts.

    Returns:
        Model response text string.

    Raises:
        groq.RateLimitError: After all retries exhausted.
        groq.APIError: On non-retryable API errors.
    """
    delay = LLM_RETRY_BASE_DELAY
    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            response = _client.chat.completions.create(
                model=LLM_MODEL,   # openai/gpt-oss-120b via Groq
                messages=messages,
                temperature=0.0,   # deterministic — facts only
                max_tokens=LLM_MAX_TOKENS,
                stop=None,
            )
            return response.choices[0].message.content or ""

        except RateLimitError as e:
            if attempt == LLM_MAX_RETRIES:
                logger.error("Rate limit exhausted after %d retries.", LLM_MAX_RETRIES)
                raise
            logger.warning(
                "429 RateLimitError (attempt %d/%d). Retrying in %.0fs…",
                attempt, LLM_MAX_RETRIES, delay,
            )
            time.sleep(delay)
            delay *= 2   # exponential backoff: 2 → 4 → 8 seconds

        except Exception as e:
            # Surface non-rate-limit errors immediately (auth, network, etc.)
            logger.error("Groq API error: %s", e)
            raise

    return ""  # unreachable, but satisfies type checker


@lru_cache(maxsize=LLM_CACHE_SIZE)
def _cached_call(prompt_hash: str, prompt: str) -> str:
    """
    Cached wrapper around _call_with_retry for the main RAG pipeline.

    lru_cache keys on prompt_hash (a SHA-256 hex digest of the prompt),
    avoiding the cost of hashing the full prompt string on every cache hit.
    prompt is passed through only to build the messages list.

    Args:
        prompt_hash: SHA-256 digest of *prompt* (used as cache key).
        prompt:      Full prompt string for the LLM.

    Returns:
        Cached or freshly computed response string.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are a facts-only mutual fund FAQ assistant. "
                "Follow all rules in the user prompt strictly."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    return _call_with_retry(messages)


def call_llm(prompt: str) -> str:
    """
    Send the full RAG prompt to Groq and return the model's response text.

    Results are cached by prompt content — identical queries never hit the
    API twice. Cache holds LLM_CACHE_SIZE (256) unique prompts.

    Args:
        prompt: Full prompt string (system instructions + context + query).

    Returns:
        Model's response as a plain string (empty string if LLM refused).

    Raises:
        groq.RateLimitError: If rate limit is exhausted after all retries.
    """
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
    return _cached_call(prompt_hash, prompt)


def call_llm_raw(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 10,
) -> str:
    """
    Lightweight Groq call with custom system prompt.

    Used by the Tier-2 classifier for zero-shot intent classification.
    Not cached (classification queries are short and vary per user input).

    Args:
        system_prompt: System-role instructions.
        user_message:  The user's raw query to classify.
        max_tokens:    Maximum tokens in the response (default 10).

    Returns:
        Raw model output string (stripped). Empty string on failure.
    """
    try:
        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.0,
            max_tokens=max_tokens,
            stop=None,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception:
        return ""


def cache_info() -> str:
    """Return a human-readable LRU cache statistics string."""
    info = _cached_call.cache_info()
    return (
        f"LRU cache: {info.hits} hits / {info.misses} misses / "
        f"{info.currsize}/{info.maxsize} slots used"
    )
