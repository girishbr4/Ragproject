# Edge Cases: Mutual Fund FAQ Assistant

> **Project:** Facts-Only FAQ Assistant – HDFC Mutual Fund Schemes (RAG + Groq)
> **Disclaimer:** Facts-only. No investment advice.

---

## Overview

This document catalogues every known and anticipated edge case across all pipeline stages of the RAG-based FAQ assistant. Each edge case includes:

- **Trigger** — what causes it
- **Risk** — what goes wrong if unhandled
- **Expected Behaviour** — what the system should do
- **Handling** — where in the code it is addressed
- **Test Input / Output** — concrete example for testing

Edge cases are grouped by the pipeline layer in which they originate.

---

## Category Index

| # | Category |
|---|---|
| 1 | [Query Classification Edge Cases](#1-query-classification-edge-cases) |
| 2 | [PII & Privacy Edge Cases](#2-pii--privacy-edge-cases) |
| 3 | [Retrieval Engine Edge Cases](#3-retrieval-engine-edge-cases) |
| 4 | [LLM Output Edge Cases](#4-llm-output-edge-cases) |
| 5 | [Data Ingestion Edge Cases](#5-data-ingestion-edge-cases) |
| 6 | [Groq API Edge Cases](#6-groq-api-edge-cases) |
| 7 | [UI & Session Edge Cases](#7-ui--session-edge-cases) |
| 8 | [Compliance & Response Format Edge Cases](#8-compliance--response-format-edge-cases) |

---

## 1. Query Classification Edge Cases

### EC-1.1 — Advisory query disguised as factual

| Field | Detail |
|---|---|
| **Trigger** | User phrases an advisory query to sound factual |
| **Example input** | `"Factually speaking, which HDFC fund is the best for me?"` |
| **Risk** | Regex classifier misses it; advisory response generated |
| **Expected behaviour** | Classified as `advisory` → polite refusal + AMFI link |
| **Handling** | Tier-2 LLM zero-shot classifier catches intent beyond keyword match |

---

### EC-1.2 — Factual query with advisory-sounding words

| Field | Detail |
|---|---|
| **Trigger** | Query mentions "returns" or "performance" but is factual |
| **Example input** | `"What benchmark does HDFC Mid Cap track for performance measurement?"` |
| **Risk** | Regex over-triggers on "performance" → false refusal |
| **Expected behaviour** | Classified as `factual` → retrieval + answer with benchmark name |
| **Handling** | Regex uses `\breturns\b` not `\bperformance\b`; LLM tier-2 resolves ambiguity |

---

### EC-1.3 — Multi-intent query (factual + advisory combined)

| Field | Detail |
|---|---|
| **Trigger** | Single query mixes both a factual question and advice-seeking |
| **Example input** | `"What is the expense ratio of HDFC ELSS and should I invest in it?"` |
| **Risk** | Classifier picks only one intent; advisory part answered |
| **Expected behaviour** | Classify as `advisory`; answer the factual part + append refusal for advisory part |
| **Handling** | Classifier returns `advisory` on any advisory signal; system prompt directs LLM to answer factual portion only then add refusal note |

---

### EC-1.4 — Non-English / transliterated query

| Field | Detail |
|---|---|
| **Trigger** | User types in transliterated Hindi or regional language |
| **Example input** | `"HDFC ELSS ka lock-in period kya hai?"` |
| **Risk** | Regex classifier fails; embedding quality degrades |
| **Expected behaviour** | Attempt retrieval; if confidence low → "Please ask in English" message |
| **Handling** | Similarity threshold acts as quality gate; fallback message triggered |

---

### EC-1.5 — Empty or whitespace-only query

| Field | Detail |
|---|---|
| **Trigger** | User submits empty input or only spaces |
| **Example input** | `"   "` or `""` |
| **Risk** | Embedding fails on empty string; pipeline crashes |
| **Expected behaviour** | Input validation before classifier; show "Please enter a question" |
| **Handling** | `if not query.strip(): return "Please enter a question."` in orchestrator |

---

### EC-1.6 — Extremely long query

| Field | Detail |
|---|---|
| **Trigger** | User pastes a very long paragraph as a query |
| **Example input** | 500+ word paragraph about mutual funds |
| **Risk** | Groq token limit exceeded; embedding is noisy |
| **Expected behaviour** | Truncate query to first 300 characters before processing; notify user |
| **Handling** | Pre-processing step: `query = query[:300]` with warning shown |

---

### EC-1.7 — Query about a non-HDFC AMC

| Field | Detail |
|---|---|
| **Trigger** | Query references a different fund house |
| **Example input** | `"What is the expense ratio of SBI Blue Chip Fund?"` |
| **Risk** | Retrieval returns no relevant chunks; LLM hallucinates an answer |
| **Expected behaviour** | Low similarity score → fallback: "This assistant only covers HDFC schemes." |
| **Handling** | Empty retrieval fallback in `pipeline/main.py` with scope message |

**Fallback response:**
```
This assistant covers only HDFC Mutual Fund schemes.
For SBI Mutual Fund information, please visit: https://www.sbimf.com

> Facts-only. No investment advice.
```

---

### EC-1.8 — Performance prediction query

| Field | Detail |
|---|---|
| **Trigger** | User asks about future returns |
| **Example input** | `"Will HDFC Mid Cap give 15% returns next year?"` |
| **Risk** | LLM speculates on future returns |
| **Expected behaviour** | Classified as advisory → refusal + link to official factsheet |
| **Handling** | `\breturns\b` + `\bnext year\b` pattern in regex classifier |

---

## 2. PII & Privacy Edge Cases

### EC-2.1 — PAN number in query

| Field | Detail |
|---|---|
| **Trigger** | Query contains a PAN-format string |
| **Example input** | `"My PAN is ABCDE1234F, what is my folio status?"` |
| **Risk** | PII processed/logged; privacy violation |
| **Expected behaviour** | PII guard fires before any processing; PII rejection message returned |
| **Regex** | `\b[A-Z]{5}[0-9]{4}[A-Z]\b` |
| **Handling** | `classify()` in `pipeline/classifier.py`; no data stored |

---

### EC-2.2 — Aadhaar number in query

| Field | Detail |
|---|---|
| **Trigger** | Query contains a 12-digit number |
| **Example input** | `"My Aadhaar is 1234 5678 9012, check my KYC"` |
| **Risk** | Aadhaar number sent to Groq API; privacy breach |
| **Expected behaviour** | PII guard intercepts before `call_llm()` is ever called |
| **Regex** | `\b\d{12}\b` |

---

### EC-2.3 — Phone number in query

| Field | Detail |
|---|---|
| **Trigger** | Query contains a 10-digit Indian mobile number |
| **Example input** | `"Call me at 9876543210 with fund details"` |
| **Risk** | Phone number forwarded to LLM |
| **Expected behaviour** | PII refusal |
| **Regex** | `\b[6-9]\d{9}\b` (Indian mobile format) |

---

### EC-2.4 — Email address in query

| Field | Detail |
|---|---|
| **Trigger** | User includes email in query |
| **Example input** | `"Send the SIP details to user@example.com"` |
| **Risk** | Email stored or sent to LLM |
| **Expected behaviour** | PII rejection; prompt user to rephrase |
| **Regex** | `\b[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}\b` |

---

### EC-2.5 — PII in LLM output (output leakage)

| Field | Detail |
|---|---|
| **Trigger** | LLM response unexpectedly contains PII-like content (e.g., from training data) |
| **Risk** | PII surfaced to user in response |
| **Expected behaviour** | Response formatter runs PII scan on output before returning |
| **Handling** | Post-process `format_response()` strips PII-matching patterns from `raw` output |

---

## 3. Retrieval Engine Edge Cases

### EC-3.1 — No chunks above similarity threshold

| Field | Detail |
|---|---|
| **Trigger** | Query is too vague or unrelated; all similarity scores below `SIMILARITY_THRESHOLD = 0.35` |
| **Example input** | `"Tell me about cryptocurrency"` |
| **Risk** | LLM makes up an answer using general knowledge |
| **Expected behaviour** | `retrieve()` returns empty list → fallback response triggered |
| **Handling** | `if not chunks:` guard in `pipeline/main.py` |

**Fallback response:**
```
I could not find this information in the official HDFC sources.
Please visit https://www.amfiindia.com for more details.

> Facts-only. No investment advice.
Last updated from sources: 2025-08-27
```

---

### EC-3.2 — Retrieved chunks from wrong scheme

| Field | Detail |
|---|---|
| **Trigger** | Query mentions HDFC ELSS but retriever returns HDFC Large Cap chunks due to semantic overlap |
| **Risk** | Answer mixes data from two different schemes |
| **Expected behaviour** | Scheme name extracted from query and used as a metadata filter |
| **Handling** | Add ChromaDB `where={"scheme_name": detected_scheme}` filter when scheme is identifiable |

---

### EC-3.3 — Stale vector store (outdated data)

| Field | Detail |
|---|---|
| **Trigger** | Expense ratios or exit loads changed since last scrape |
| **Risk** | System returns outdated facts |
| **Expected behaviour** | Date footer shows scrape date clearly; user can see data age |
| **Handling** | Every chunk stores `scrape_date`; footer shows `"Last updated from sources: <date>"` |

---

### EC-3.4 — ChromaDB collection missing or corrupted

| Field | Detail |
|---|---|
| **Trigger** | `vector_store/chroma_db/` directory missing or deleted |
| **Risk** | `client.get_collection()` raises exception; app crashes |
| **Expected behaviour** | Graceful error: "Knowledge base not available. Please run `python ingest_all.py` first." |
| **Handling** | Try/except around `client.get_collection()` in `retriever.py` |

---

### EC-3.5 — Duplicate chunks ingested

| Field | Detail |
|---|---|
| **Trigger** | `ingest_all.py` run twice without resetting collection |
| **Risk** | Same chunk returned multiple times; inflated context |
| **Expected behaviour** | Idempotent ingestion: clear collection before re-ingesting, or use chunk IDs to dedup |
| **Handling** | Use deterministic `id = hash(source_url + chunk_text)` as ChromaDB document ID |

---

## 4. LLM Output Edge Cases

### EC-4.1 — LLM response exceeds 3 sentences

| Field | Detail |
|---|---|
| **Trigger** | Groq model generates a verbose answer despite `max_tokens=300` |
| **Risk** | Response violates problem statement constraint |
| **Expected behaviour** | `format_response()` splits on sentence boundaries and truncates to 3 |
| **Handling** | `sentences = re.split(r'(?<=[.?!])\s+', raw); trimmed = " ".join(sentences[:3])` |

---

### EC-4.2 — LLM omits the source citation

| Field | Detail |
|---|---|
| **Trigger** | Model forgets to append `Source:` despite system prompt instruction |
| **Risk** | Response has no citation; compliance violation |
| **Expected behaviour** | Formatter detects missing `Source:` and injects `chunks[0]["source_url"]` |
| **Handling** | `if "Source:" not in trimmed: trimmed += f"\nSource: {source_url}"` |

---

### EC-4.3 — LLM omits date footer

| Field | Detail |
|---|---|
| **Trigger** | Model drops the `"Last updated from sources: <date>"` footer |
| **Risk** | Response has no date; user cannot assess data freshness |
| **Expected behaviour** | Formatter injects footer from chunk metadata |
| **Handling** | `if "Last updated" not in trimmed: trimmed += f"\nLast updated from sources: {date}"` |

---

### EC-4.4 — LLM hallucinates a specific number (e.g., wrong expense ratio)

| Field | Detail |
|---|---|
| **Trigger** | System prompt is followed but context chunk is ambiguous or truncated |
| **Risk** | Factually incorrect number returned to user |
| **Expected behaviour** | `temperature=0.0` minimises drift; strict system prompt enforces context-only answering |
| **Handling** | System prompt rule 1: "Answer ONLY using the CONTEXT. Never infer or hallucinate." |
| **Mitigation** | Use `max_tokens=300` and `temperature=0.0` on Groq call |

---

### EC-4.5 — LLM provides investment advice despite system prompt

| Field | Detail |
|---|---|
| **Trigger** | Model subtly slips in a recommendation within a factual response |
| **Risk** | Compliance violation; potential legal liability |
| **Expected behaviour** | Post-processing scans for advisory language patterns and strips/replaces them |
| **Advisory phrases to detect** | `"you should"`, `"I recommend"`, `"consider investing"`, `"great choice"` |
| **Handling** | Advisory pattern scan in `format_response()` before returning |

```python
ADVISORY_LEAK_PATTERNS = [
    r"\byou should\b", r"\bi recommend\b", r"\bconsider investing\b",
    r"\bgreat choice\b", r"\bgood option\b"
]
def scan_advisory_leak(text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in ADVISORY_LEAK_PATTERNS)
```

---

### EC-4.6 — LLM responds in a different language

| Field | Detail |
|---|---|
| **Trigger** | Groq model responds in Hindi or another language (rare) |
| **Risk** | User receives non-English response; consistency broken |
| **Expected behaviour** | System prompt explicitly states: "Always respond in English." |
| **Handling** | Add `"Always respond in English."` to system prompt |

---

## 5. Data Ingestion Edge Cases

### EC-5.1 — Groww page is down or returns 403/404

| Field | Detail |
|---|---|
| **Trigger** | Scraper hits `requests.get()` and gets a non-200 response |
| **Risk** | Scraper silently stores empty content; chunks are blank |
| **Expected behaviour** | Log error; skip that URL; use previously cached raw HTML if available |
| **Handling** | `if response.status_code != 200: log_warning(); use_cache()` |

---

### EC-5.2 — Groww page layout changes (DOM structure changes)

| Field | Detail |
|---|---|
| **Trigger** | Groww redesigns its scheme pages; CSS selectors break |
| **Risk** | Scraper extracts empty strings; knowledge base becomes stale |
| **Expected behaviour** | Scraper raises a `ScraperValidationError` if extracted fields are empty |
| **Handling** | Field validation: `assert scheme_data["expense_ratio"], "Expense ratio not found"` |

---

### EC-5.3 — AMFI PDF is a scanned image (non-text PDF)

| Field | Detail |
|---|---|
| **Trigger** | AMFI factsheet uploaded as a scanned image PDF rather than text-based |
| **Risk** | `PyMuPDF` returns empty string; no content ingested |
| **Expected behaviour** | Detect zero-text extraction → log warning; skip PDF; note limitation in metadata |
| **Handling** | `if len(text.strip()) < 50: log_warning("Scanned PDF detected")` |

---

### EC-5.4 — Chunk text too short (< 50 tokens)

| Field | Detail |
|---|---|
| **Trigger** | Text splitter creates micro-chunks (headings, single values) |
| **Risk** | Chunk has insufficient context for retrieval; noisy results |
| **Expected behaviour** | Filter out chunks shorter than 50 tokens during ingestion |
| **Handling** | `chunks = [c for c in chunks if len(c["text"].split()) >= 50]` |

---

### EC-5.5 — Metadata.json missing or malformed

| Field | Detail |
|---|---|
| **Trigger** | `data/metadata.json` deleted or corrupted |
| **Risk** | Date footer shows "N/A"; source tracking lost |
| **Expected behaviour** | Graceful fallback to chunk-level metadata from ChromaDB |
| **Handling** | Each chunk in ChromaDB stores its own `source_url` and `date` in metadata |

---

## 6. Groq API Edge Cases

### EC-6.1 — Groq API key missing or invalid

| Field | Detail |
|---|---|
| **Trigger** | `GROQ_API_KEY` not set in `.env` or is expired |
| **Risk** | `AuthenticationError` raised; app crashes |
| **Expected behaviour** | Startup check validates key; clear error message shown |
| **Handling** | `if not os.environ.get("GROQ_API_KEY"): raise EnvironmentError("GROQ_API_KEY not set")` |

---

### EC-6.2 — Groq rate limit hit (429 Too Many Requests)

| Field | Detail |
|---|---|
| **Trigger** | Free tier RPM/RPD quota exceeded |
| **Risk** | `RateLimitError`; app crashes or hangs |
| **Expected behaviour** | Catch `RateLimitError`; show user a retry message; exponential back-off |
| **Handling** | Wrap `call_llm()` in retry logic with `time.sleep(2 ** attempt)` |

```python
import time
from groq import RateLimitError

def call_llm_with_retry(prompt: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            return call_llm(prompt)
        except RateLimitError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)   # 1s, 2s, 4s
            else:
                return ("The assistant is temporarily unavailable due to high demand. "
                        "Please try again in a moment.\n\n> Facts-only. No investment advice.")
```

---

### EC-6.3 — Groq API timeout

| Field | Detail |
|---|---|
| **Trigger** | Network timeout or Groq infrastructure latency |
| **Risk** | Request hangs indefinitely; UI freezes |
| **Expected behaviour** | Timeout after 15 seconds; return a friendly error message |
| **Handling** | Set `timeout=15` on Groq client instantiation |

---

### EC-6.4 — Groq returns an empty response

| Field | Detail |
|---|---|
| **Trigger** | Model returns empty string (rare but possible) |
| **Risk** | Formatter crashes on empty string; UI shows blank response |
| **Expected behaviour** | Detect empty response; return fallback message |
| **Handling** | `if not raw or not raw.strip(): return fallback_response` |

---

### EC-6.5 — Context window overflow (prompt too long)

| Field | Detail |
|---|---|
| **Trigger** | System prompt + 4 retrieved chunks + query exceeds Groq model context window |
| **Risk** | `context_length_exceeded` error from API |
| **Expected behaviour** | Reduce TOP_K from 4 to 2; trim chunks to 200 tokens each before prompt assembly |
| **Handling** | Pre-compute prompt length; truncate oldest/least-relevant chunks if > 4096 tokens |

---

## 7. UI & Session Edge Cases

### EC-7.1 — User clicks example button multiple times rapidly

| Field | Detail |
|---|---|
| **Trigger** | User clicks an example question button before the previous response completes |
| **Risk** | Two simultaneous Groq API calls; race condition in session state |
| **Expected behaviour** | Disable input/buttons while a response is being generated |
| **Handling** | Use `st.session_state["loading"] = True` to disable buttons during response |

---

### EC-7.2 — Very long conversation history

| Field | Detail |
|---|---|
| **Trigger** | User has a 50+ message chat session |
| **Risk** | Streamlit session state grows; page re-renders become slow |
| **Expected behaviour** | Cap chat history display to last 20 messages |
| **Handling** | `messages_to_show = st.session_state["messages"][-20:]` |

---

### EC-7.3 — User copies and submits a previous response as a query

| Field | Detail |
|---|---|
| **Trigger** | User pastes assistant response (which includes `Source:` URL) as new query |
| **Risk** | Classifier may misfire; URL passed as query |
| **Expected behaviour** | Normal retrieval; response will be low-similarity → graceful fallback |

---

### EC-7.4 — Browser back navigation clears Streamlit session

| Field | Detail |
|---|---|
| **Trigger** | User navigates away and returns |
| **Risk** | Chat history lost; user confused |
| **Expected behaviour** | Session state resets to empty (expected Streamlit behaviour); welcome message shows again |

---

## 8. Compliance & Response Format Edge Cases

### EC-8.1 — Source URL in retrieved chunk is broken / returns 404

| Field | Detail |
|---|---|
| **Trigger** | Groww or AMC changes a page URL after ingestion |
| **Risk** | Response cites a dead link |
| **Expected behaviour** | URL validation at ingestion time; flag broken URLs in `metadata.json` |
| **Handling** | Run `requests.head(url)` during ingestion; mark `"url_valid": false` if 404 |

---

### EC-8.2 — Third-party domain leaks into source URL

| Field | Detail |
|---|---|
| **Trigger** | Chunk metadata accidentally stores a non-whitelisted URL |
| **Risk** | Response cites a blog or aggregator; compliance violation |
| **Expected behaviour** | Formatter validates `source_url` against `WHITELISTED_DOMAINS` before injection |
| **Handling** | `assert any(d in source_url for d in WHITELISTED_DOMAINS)` in formatter |

---

### EC-8.3 — Response contains a performance comparison

| Field | Detail |
|---|---|
| **Trigger** | Two scheme names appear in same query |
| **Example input** | `"What is the difference in expense ratio between HDFC Mid Cap and HDFC Small Cap?"` |
| **Risk** | LLM provides a comparison; compliance violation |
| **Expected behaviour** | Classify as advisory/comparison → refusal with factsheet links for both schemes |
| **Handling** | Detect multi-scheme queries in classifier; route to refusal |

---

### EC-8.4 — Date footer shows wrong or future date

| Field | Detail |
|---|---|
| **Trigger** | System clock misconfigured; `scrape_date` stored incorrectly |
| **Risk** | User sees a future date in footer; credibility issue |
| **Expected behaviour** | Validate `scrape_date` at ingestion: reject if date > `datetime.date.today()` |
| **Handling** | `assert scrape_date <= datetime.date.today().isoformat()` in embedder |

---

## Summary Table

| ID | Category | Trigger | Severity | Handled By |
|---|---|---|---|---|
| EC-1.1 | Classifier | Advisory query disguised as factual | 🔴 High | LLM tier-2 classifier |
| EC-1.2 | Classifier | False advisory trigger on factual query | 🟡 Medium | Regex tuning + LLM fallback |
| EC-1.3 | Classifier | Multi-intent query | 🔴 High | Advisory-first classification rule |
| EC-1.4 | Classifier | Non-English query | 🟡 Medium | Similarity threshold fallback |
| EC-1.5 | Classifier | Empty query | 🟡 Medium | Input validation in orchestrator |
| EC-1.6 | Classifier | Extremely long query | 🟡 Medium | Query truncation to 300 chars |
| EC-1.7 | Classifier | Non-HDFC scheme query | 🟡 Medium | Empty retrieval fallback |
| EC-1.8 | Classifier | Performance prediction query | 🔴 High | Regex + refusal handler |
| EC-2.1 | PII | PAN in query | 🔴 High | PII guard in classifier |
| EC-2.2 | PII | Aadhaar in query | 🔴 High | PII guard in classifier |
| EC-2.3 | PII | Phone number in query | 🔴 High | PII guard in classifier |
| EC-2.4 | PII | Email in query | 🟡 Medium | PII guard in classifier |
| EC-2.5 | PII | PII in LLM output | 🔴 High | Output PII scan in formatter |
| EC-3.1 | Retrieval | No chunks above threshold | 🟡 Medium | Empty-list fallback in main.py |
| EC-3.2 | Retrieval | Wrong scheme chunks returned | 🟡 Medium | ChromaDB metadata filter |
| EC-3.3 | Retrieval | Stale vector store | 🟢 Low | Date footer transparency |
| EC-3.4 | Retrieval | ChromaDB missing/corrupted | 🔴 High | Try/except + user error message |
| EC-3.5 | Retrieval | Duplicate chunks | 🟢 Low | Deterministic chunk IDs |
| EC-4.1 | LLM Output | Response > 3 sentences | 🟡 Medium | Formatter truncation |
| EC-4.2 | LLM Output | Missing source citation | 🔴 High | Formatter citation injection |
| EC-4.3 | LLM Output | Missing date footer | 🟡 Medium | Formatter footer injection |
| EC-4.4 | LLM Output | Hallucinated number | 🔴 High | temperature=0.0 + context-only prompt |
| EC-4.5 | LLM Output | Investment advice leakage | 🔴 High | Advisory pattern scan in formatter |
| EC-4.6 | LLM Output | Non-English response | 🟢 Low | "Always respond in English" in prompt |
| EC-5.1 | Ingestion | Scraper 403/404 | 🟡 Medium | Cache fallback + error log |
| EC-5.2 | Ingestion | DOM structure change | 🟡 Medium | Field validation assertions |
| EC-5.3 | Ingestion | Scanned image PDF | 🟡 Medium | Zero-text detection + skip |
| EC-5.4 | Ingestion | Micro-chunks (< 50 tokens) | 🟢 Low | Chunk length filter |
| EC-5.5 | Ingestion | metadata.json missing | 🟢 Low | ChromaDB per-chunk metadata fallback |
| EC-6.1 | Groq API | Missing/invalid API key | 🔴 High | Startup env check |
| EC-6.2 | Groq API | Rate limit (429) | 🟡 Medium | Exponential back-off retry |
| EC-6.3 | Groq API | API timeout | 🟡 Medium | 15s timeout on client |
| EC-6.4 | Groq API | Empty response | 🟡 Medium | Empty response guard |
| EC-6.5 | Groq API | Context window overflow | 🟡 Medium | Prompt length check + chunk trim |
| EC-7.1 | UI | Rapid button clicks | 🟢 Low | Loading state lock |
| EC-7.2 | UI | Long conversation history | 🟢 Low | Cap display at 20 messages |
| EC-7.3 | UI | Response pasted as query | 🟢 Low | Similarity fallback |
| EC-7.4 | UI | Browser navigation resets session | 🟢 Low | Expected behaviour |
| EC-8.1 | Compliance | Broken source URL | 🟡 Medium | URL validation at ingestion |
| EC-8.2 | Compliance | Non-whitelisted source URL | 🔴 High | Domain whitelist check in formatter |
| EC-8.3 | Compliance | Performance comparison query | 🔴 High | Multi-scheme detection → refusal |
| EC-8.4 | Compliance | Wrong date in footer | 🟡 Medium | Date validation at ingestion |

---

## Severity Legend

| Icon | Level | Meaning |
|---|---|---|
| 🔴 | High | Could cause compliance violation, privacy breach, or app crash |
| 🟡 | Medium | Degrades accuracy or user experience; must be handled |
| 🟢 | Low | Minor UX issue; handle if time permits |

---

> **Disclaimer:** Facts-only. No investment advice.

