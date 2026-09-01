# Implementation Plan: Mutual Fund FAQ Assistant (RAG-Based)

> **Project:** Facts-Only FAQ Assistant for HDFC Mutual Fund Schemes
> **AMC:** HDFC Mutual Fund | **Reference platform:** Groww
> **Approach:** Retrieval-Augmented Generation (RAG)
> **Disclaimer:** Facts-only. No investment advice.

---

## Overview

This plan breaks the build into **6 sequential phases**, each delivering a testable milestone. Phases 1–3 cover the offline data pipeline; Phases 4–5 build the runtime query engine and UI; Phase 6 covers hardening, compliance verification, and documentation.

```
Phase 1 ─ Environment & Project Setup          (Day 1)
Phase 2 ─ Data Ingestion & Knowledge Base      (Day 2–3)
Phase 3 ─ Embedding & Vector Store             (Day 4)
Phase 4 ─ RAG Query Pipeline                   (Day 5–6)
Phase 5 ─ Frontend UI                          (Day 7)
Phase 6 ─ Testing, Hardening & Documentation   (Day 8–9)
Phase 7 ─ Daily Scheduler & Auto-Update        (Day 10)
```

---

## Phase 1 — Environment & Project Setup

**Goal:** Establish the project scaffold, dependencies, and configuration before writing any functional code.

### 1.1 Repository & Folder Structure

Create the following layout (matching `architecture.md §9`):

```
ragchatbot/
├── data/
│   ├── raw/
│   ├── processed/
│   └── metadata.json
├── ingestion/
│   ├── scraper.py
│   ├── pdf_parser.py
│   ├── chunker.py
│   └── embedder.py
├── retrieval/
│   ├── retriever.py
│   └── reranker.py
├── pipeline/
│   ├── classifier.py
│   ├── prompt_builder.py
│   ├── llm_client.py
│   ├── response_formatter.py
│   └── refusal_handler.py
├── scheduler/
│   ├── daily_update.py      ← Orchestrates the daily scrape → embed → update cycle
│   ├── scheduler_runner.py  ← APScheduler process entry point
│   └── notifier.py          ← Optional: sends email/Slack alert on run status
├── ui/
│   ├── app.py
│   └── static/
├── vector_store/
│   └── chroma_db/
├── logs/
│   └── scheduler.log        ← Rolling log file for all scheduler runs
├── config.py
├── requirements.txt
├── problemstatement.md
├── architecture.md
├── implementation-plan.md
└── README.md
```

### 1.2 Python Environment

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install --upgrade pip
```

### 1.3 Install Dependencies (`requirements.txt`)

| Package | Purpose |
|---|---|
| `langchain` | RAG pipeline orchestration |
| `langchain-community` | ChromaDB, document loaders |
| `chromadb` | Local vector store |
| `sentence-transformers` | Local embedding model (`all-MiniLM-L6-v2`) |
| `groq` | Groq API client for LLM inference |
| `beautifulsoup4` | HTML scraping |
| `requests` | HTTP client for scraping |
| `playwright` | Dynamic JS page scraping (optional) |
| `lxml` | Faster HTML parsing backend for BeautifulSoup |
| `streamlit` | Minimal UI layer |
| `python-dotenv` | API key management |
| `pytest` | Unit and integration tests |

### 1.4 Configuration (`config.py`)

```python
# config.py
import os
from dotenv import load_dotenv
load_dotenv()

LLM_PROVIDER       = "groq"                 # Groq API
LLM_MODEL          = "openai/gpt-oss-120b"      # Groq-hosted OpenAI-compatible model
EMBEDDING_MODEL    = "BAAI/bge-small-en-v1.5"   # BGE small — outperforms MiniLM on retrieval benchmarks
CHROMA_DB_PATH     = "vector_store/chroma_db"
CHUNK_SIZE         = 400                    # tokens
CHUNK_OVERLAP      = 60
TOP_K              = 4                      # retrieval chunks
SIMILARITY_THRESHOLD = 0.35
MAX_RESPONSE_SENTENCES = 3

WHITELISTED_DOMAINS = [
    "groww.in",
    "amfiindia.com",
    "sebi.gov.in",
    "hdfcfund.com",
    "camsonline.com",
    "kfintech.com"
]

SCHEME_URLS = [
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
]
```

### ✅ Phase 1 Deliverable
- Project folder created with all empty module files
- `requirements.txt` installed without errors
- `config.py` with all constants and scheme URLs
- `.env` file with API keys (not committed to version control)

---

## Phase 2 — Data Ingestion & Knowledge Base

**Goal:** Scrape, clean, and chunk content from the **5 Groww scheme pages** into the `data/processed/` directory. Groww displays all required factual fields (expense ratio, exit load, SIP minimum, riskometer, benchmark, lock-in) directly on each scheme page — no PDFs or external documents needed.

### 2.1 Web Scraper (`ingestion/scraper.py`)

Scrape the 5 HDFC scheme pages from Groww. For each page, extract:

| Field | CSS / XPath target |
|---|---|
| Scheme name | Page `<h1>` |
| Fund category | Info card |
| Expense ratio | Dedicated ratio block |
| Exit load | Exit load section |
| Minimum SIP | Investment details table |
| Minimum lump sum | Investment details table |
| Riskometer | Risk label element |
| Benchmark index | Scheme details section |
| Fund manager | Manager name element |
| Lock-in period | Displayed for ELSS only |

**Key rules:**
- Only fetch from domains in `WHITELISTED_DOMAINS`
- Store raw HTML to `data/raw/<scheme_slug>.html`
- Log scrape timestamp to `data/metadata.json`

```python
# ingestion/scraper.py  (skeleton)
import requests
from bs4 import BeautifulSoup
from config import SCHEME_URLS, WHITELISTED_DOMAINS
from urllib.parse import urlparse
import json, datetime

def is_allowed(url):
    return any(d in urlparse(url).netloc for d in WHITELISTED_DOMAINS)

def scrape_scheme(url: str) -> dict:
    assert is_allowed(url), f"Domain not whitelisted: {url}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, "html.parser")
    # ... field extraction logic ...
    return {"url": url, "scraped_at": datetime.date.today().isoformat(), "content": ...}
```

### 2.2 Text Cleaner & Chunker (`ingestion/chunker.py`)

```python
# ingestion/chunker.py  (skeleton)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " "]
)

def chunk_document(text: str, source_url: str, scrape_date: str) -> list[dict]:
    chunks = splitter.split_text(text)
    return [
        {"text": c, "source_url": source_url, "date": scrape_date}
        for c in chunks
    ]
```

**Chunking strategy:**
- Chunk size: **400 tokens**, overlap: **60 tokens**
- Preserve sentence boundaries — use `. ` as a preferred split point
- Each chunk carries metadata: `source_url`, `scrape_date`, `scheme_name`, **`chunk_type`**

**`chunk_type` classification (derived from chunk analysis of `data/processed/`):**

> [!IMPORTANT]
> Inspection of the actual processed JSON files reveals that each scheme page produces ~66–79 chunks, of which only ~5–10 are factually useful. The majority are Groww UI noise. `chunk_type` tagging is essential for retrieval quality.

| `chunk_type` value | Index range (approx.) | Content description | Used in retrieval? |
|---|---|---|---|
| `"structured_facts"` | 0–2 | Key-facts block: expense ratio, SIP, risk, benchmark, fund manager, lock-in | ✅ **Highest priority** |
| `"faq_text"` | ~50–60 | FAQ paragraphs with factual sentences (Expense Ratio is X%, AUM is Y Cr) | ✅ Secondary |
| `"fund_description"` | ~48–55 | Investment objective, scheme description | ✅ Tertiary |
| `"holdings"` | ~11–45 | Portfolio holdings: stock names, sectors, percentages | ⚠️ Only for holding-specific queries |
| `"noise"` | ~3–10, ~60–79 | Groww nav menus, footer links, commodity futures, calculator links, fund ads | ❌ **Excluded from retrieval** |

**Noise detection heuristics (applied in `chunker.py`):**
```python
NOISE_MARKERS = [
    "--- Full Page Content ---",  # explicit separator chunk
    "Trade in Futures",
    "Login/Sign up",
    "Download the App",
    "© 2016-",
    "Ctrl+K",
    "Groww IFSC",
    "Gold Petal Future",
    "SIP Calculator",   # footer calculator links
    "NSE\nBSE\nMCX",
]

def classify_chunk_type(text: str, chunk_index: int) -> str:
    if chunk_index == 0:  # always the scheme header chunk
        return "structured_facts"
    if chunk_index == 1:  # always the structured key-facts block
        return "structured_facts"
    if "Lock-in Period" in text:  # ELSS lock-in chunk
        return "structured_facts"
    if any(marker in text for marker in NOISE_MARKERS):
        return "noise"
    if "Expense Ratio of" in text or "AUM" in text or "NAV of" in text:
        return "faq_text"
    if "Investment Objective" in text or "seeks to provide" in text:
        return "fund_description"
    # Holdings chunks: contain repeated pattern of stock\nSector\nEquity\n%
    if text.count("\nEquity\n") >= 3 or text.count("\nFinancial\n") >= 2:
        return "holdings"
    return "faq_text"  # default for remaining page body
```

**Updated `chunk_document` function:**
```python
def chunk_document(text: str, source_url: str, scrape_date: str, scheme_name: str) -> list[dict]:
    chunks = splitter.split_text(text)
    result = []
    for i, c in enumerate(chunks):
        chunk_type = classify_chunk_type(c, i)
        result.append({
            "text": c,
            "source_url": source_url,
            "date": scrape_date,
            "scheme_name": scheme_name,
            "chunk_type": chunk_type,
        })
    return result
```

### 2.3 Metadata Registry (`data/metadata.json`)

After each scrape run, update with one entry per Groww scheme page:

```json
{
  "hdfc-mid-cap": {
    "source_url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "scrape_date": "2025-08-27",
    "chunk_count": 18,
    "type": "web"
  },
  "hdfc-small-cap": {
    "source_url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    "scrape_date": "2025-08-27",
    "chunk_count": 16,
    "type": "web"
  },
  "hdfc-gold-fof": {
    "source_url": "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth",
    "scrape_date": "2025-08-27",
    "chunk_count": 14,
    "type": "web"
  },
  "hdfc-large-cap": {
    "source_url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
    "scrape_date": "2025-08-27",
    "chunk_count": 17,
    "type": "web"
  },
  "hdfc-elss": {
    "source_url": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
    "scrape_date": "2025-08-27",
    "chunk_count": 19,
    "type": "web"
  }
}
```

### ✅ Phase 2 Deliverable
- `data/raw/` contains scraped HTML for all 5 Groww scheme pages
- `data/processed/` contains cleaned, chunked `.txt` or `.json` files
- `data/metadata.json` records source URL and scrape date for all 5 Groww pages
- No PDF files, no AMFI downloads required

---

## Phase 3 — Embedding & Vector Store

**Goal:** Convert all processed chunks into dense embeddings and persist them in ChromaDB. Only **non-noise** chunks are embedded — `chunk_type == "noise"` chunks are skipped entirely.

### 3.1 Embedding Model

Use `sentence-transformers` with the `BAAI/bge-small-en-v1.5` model (local, no API cost):

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-small-en-v1.5")
embedding = model.encode("What is the expense ratio?", normalize_embeddings=True)
```

**Why `bge-small-en-v1.5` over `all-MiniLM-L6-v2`?**

| Property | `all-MiniLM-L6-v2` | `BAAI/bge-small-en-v1.5` |
|---|---|---|
| MTEB Retrieval avg | ~41.7 | ~51.7 (+24%) |
| Model size | ~22 MB | ~33 MB |
| Embedding dim | 384 | 384 |
| Max tokens | 256 | 512 |
| Instruction-tuned | ❌ | ✅ |
| Query prefix required | ❌ | At retrieval time only |
| Licence | Apache 2.0 | MIT |

**BGE encoding rules (important):**
- **At index time** (embedder.py): encode passage text as-is, no prefix
- **At query time** (retriever.py): prefix query with `"Represent this sentence for searching relevant passages: "`

This asymmetric encoding is what gives BGE its retrieval advantage.

> [!NOTE]
> Based on chunk analysis: each scheme produces ~66–79 raw chunks but only ~20–30 non-noise chunks. Filtering noise before embedding reduces ChromaDB collection size by ~55% and significantly improves retrieval precision.

### 3.2 ChromaDB Ingestion (`ingestion/embedder.py`)

```python
# ingestion/embedder.py  (skeleton)
import chromadb
from sentence_transformers import SentenceTransformer
from config import CHROMA_DB_PATH, EMBEDDING_MODEL

client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_or_create_collection("mutual_fund_facts")
model = SentenceTransformer(EMBEDDING_MODEL)  # BAAI/bge-small-en-v1.5

def ingest_chunks(chunks: list[dict], scheme_slug: str):
    """
    Embed and store only non-noise chunks.
    Stores chunk_type and scheme_name in ChromaDB metadata for
    downstream metadata-filtered retrieval.
    """
    # Filter out noise chunks before embedding
    clean_chunks = [c for c in chunks if c.get("chunk_type") != "noise"]

    texts      = [c["text"] for c in clean_chunks]
    # BGE: no prefix at index time — encode passages as-is
    embeddings = model.encode(texts, normalize_embeddings=True).tolist()
    ids        = [f"{scheme_slug}_chunk_{i}" for i in range(len(clean_chunks))]
    metadatas  = [
        {
            "source_url":  c["source_url"],
            "date":        c["date"],
            "scheme_name": c["scheme_name"],
            "chunk_type":  c["chunk_type"],   # ← stored for where-filter in retrieval
        }
        for c in clean_chunks
    ]
    collection.add(
        documents=texts,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas,
    )
```

### 3.3 Ingestion Runner

Create `ingest_all.py` at the project root to run the full ingestion pipeline:

```
python ingest_all.py
  → scrape all 5 scheme URLs
  → parse AMFI PDFs
  → clean & chunk all text
  → embed & store in ChromaDB
  → update metadata.json
```

### ✅ Phase 3 Deliverable
- ChromaDB collection `mutual_fund_facts` populated with all chunks
- Each chunk has metadata: `source_url`, `date`, `scheme_name`
- `ingest_all.py` runs end-to-end without errors
- Verify: query ChromaDB with a test similarity search and confirm relevant chunks returned

---

## Phase 4 — RAG Query Pipeline

**Goal:** Build the complete runtime pipeline — classifier → retriever → prompt builder → LLM → formatter.

### 4.1 Query Classifier (`pipeline/classifier.py`)

Two-tier classification:

**Tier 1 — Regex keyword check (fast, free):**
```python
ADVISORY_PATTERNS = [
    r"\bshould i\b", r"\bwhich fund\b", r"\bbetter\b", r"\brecommend\b",
    r"\binvest in\b", r"\bperformance\b", r"\breturns\b", r"\bbest fund\b"
]
PII_PATTERNS = [
    r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",   # PAN
    r"\b\d{12}\b",                    # Aadhaar
    r"\b\d{10}\b",                    # Phone
]

def classify(query: str) -> str:
    # returns: "advisory" | "pii" | "factual"
```

**Tier 2 — LLM zero-shot (for ambiguous queries):**
Send a tiny classification prompt to the LLM if regex confidence is low.

### 4.2 Retrieval Engine (`retrieval/retriever.py`)

> [!IMPORTANT]
> **Retrieval strategy updated based on actual chunk analysis.** The processed data has three structurally distinct chunk layers that require a multi-pass retrieval approach:
>
> | Pass | ChromaDB `where` filter | `n_results` | Purpose |
> |---|---|---|---|
> | **Pass 1 — Priority** | `chunk_type IN ["structured_facts"]` | `TOP_K` | Always fetch the golden key-facts block first |
> | **Pass 2 — Semantic** | `chunk_type IN ["faq_text", "fund_description"]` | `TOP_K` | Fetch best semantic match from FAQ/description chunks |
> | **Pass 3 — Holdings** | `chunk_type == "holdings"` | 2 | Only when query mentions holdings/portfolio |
> | *(skipped)* | `chunk_type == "noise"` | — | Never retrieved (not embedded) |

**Scheme-scoped retrieval:** When the query mentions a specific scheme name (e.g., "ELSS", "Mid Cap", "Small Cap", "Large Cap", "Gold"), scope Pass 2 and Pass 3 with an additional `scheme_name` where-filter to avoid cross-scheme pollution.

```python
# retrieval/retriever.py
import re
import chromadb
from sentence_transformers import SentenceTransformer
from config import CHROMA_DB_PATH, EMBEDDING_MODEL, TOP_K, SIMILARITY_THRESHOLD

_client     = chromadb.PersistentClient(path=CHROMA_DB_PATH)
_collection = _client.get_collection("mutual_fund_facts")
_model      = SentenceTransformer(EMBEDDING_MODEL)

# Map query keywords → ChromaDB scheme_name values
SCHEME_KEYWORD_MAP = {
    "mid cap":   "HDFC Mid Cap Fund Direct Growth",
    "midcap":    "HDFC Mid Cap Fund Direct Growth",
    "small cap": "HDFC Small Cap Fund Direct Growth",
    "smallcap":  "HDFC Small Cap Fund Direct Growth",
    "large cap": "HDFC Large Cap Fund Direct Growth",
    "largecap":  "HDFC Large Cap Fund Direct Growth",
    "gold":      "HDFC Gold ETF Fund of Fund Direct Plan Growth",
    "elss":      "HDFC ELSS Tax Saver Fund Direct Plan Growth",
    "tax saver": "HDFC ELSS Tax Saver Fund Direct Plan Growth",
}

FACTUAL_CHUNK_TYPES = ["structured_facts", "faq_text", "fund_description"]
HOLDINGS_KEYWORDS   = ["holding", "portfolio", "stock", "sector", "allocation"]


def _detect_scheme(query: str) -> str | None:
    """Return ChromaDB scheme_name if query mentions a specific HDFC scheme."""
    q = query.lower()
    for keyword, scheme_name in SCHEME_KEYWORD_MAP.items():
        if keyword in q:
            return scheme_name
    return None


def _is_holdings_query(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in HOLDINGS_KEYWORDS)


def retrieve(query: str) -> list[dict]:
    """
    Multi-pass retrieval strategy:

    Pass 1 — always fetch structured_facts chunks (golden key-facts blocks).
             These are the first 1–3 chunks of each scheme file and contain
             all structured fields: expense ratio, SIP, risk, benchmark etc.

    Pass 2 — semantic search over faq_text + fund_description chunks,
             optionally scoped to the detected scheme.

    Pass 3 — only when query is holdings-related: fetch holdings chunks.

    All passes use the similarity threshold to discard low-quality matches.
    Structured_facts results are prepended to the final list (highest priority).
    """
    query_embedding = _model.encode(query).tolist()
    detected_scheme = _detect_scheme(query)

    def _query_pass(where_filter: dict, n: int) -> list[dict]:
        results = _collection.query(
            query_embeddings=[query_embedding],
            n_results=n,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
        out = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            if dist < (1 - SIMILARITY_THRESHOLD):
                out.append({
                    "text":        doc,
                    "source_url":  meta["source_url"],
                    "date":        meta["date"],
                    "scheme_name": meta.get("scheme_name", ""),
                    "chunk_type":  meta.get("chunk_type", ""),
                })
        return out

    # --- Pass 1: structured facts (always; scope by scheme if detected) ---
    facts_filter: dict = {"chunk_type": {"$eq": "structured_facts"}}
    if detected_scheme:
        facts_filter = {
            "$and": [
                {"chunk_type":  {"$eq": "structured_facts"}},
                {"scheme_name": {"$eq": detected_scheme}},
            ]
        }
    priority_chunks = _query_pass(facts_filter, n=TOP_K)

    # --- Pass 2: semantic search over faq + description chunks ---
    semantic_filter: dict = {"chunk_type": {"$in": ["faq_text", "fund_description"]}}
    if detected_scheme:
        semantic_filter = {
            "$and": [
                {"chunk_type":  {"$in": ["faq_text", "fund_description"]}},
                {"scheme_name": {"$eq": detected_scheme}},
            ]
        }
    semantic_chunks = _query_pass(semantic_filter, n=TOP_K)

    # --- Pass 3: holdings chunks (only for holdings-specific queries) ---
    holdings_chunks: list[dict] = []
    if _is_holdings_query(query):
        holdings_filter: dict = {"chunk_type": {"$eq": "holdings"}}
        if detected_scheme:
            holdings_filter = {
                "$and": [
                    {"chunk_type":  {"$eq": "holdings"}},
                    {"scheme_name": {"$eq": detected_scheme}},
                ]
            }
        holdings_chunks = _query_pass(holdings_filter, n=2)

    # --- Merge: priority first, then semantic, then holdings ---
    # De-duplicate by text to avoid repeating the same chunk
    seen_texts: set[str] = set()
    merged: list[dict] = []
    for chunk in priority_chunks + semantic_chunks + holdings_chunks:
        if chunk["text"] not in seen_texts:
            seen_texts.add(chunk["text"])
            merged.append(chunk)

    return merged  # empty → triggers "not found" fallback in pipeline
```

**Why multi-pass retrieval?**

Single-pass similarity search over all chunk types fails for this dataset because:
- The structured key-facts chunks (index 0–2 per scheme) are dense keyword lists (`"Expense Ratio: 0.74%"`) that may score *lower* on cosine similarity than narrative FAQ sentences for many query phrasings.
- Without `chunk_type` filtering, a query like `"What is the expense ratio of HDFC Mid Cap?"` can return Groww footer/nav chunks that coincidentally match tokens ("Mutual Funds", "HDFC") but contain zero factual content.
- Scheme-scoping prevents cross-contamination where a Mid Cap query returns Gold FoF facts.

### 4.3 Prompt Builder (`pipeline/prompt_builder.py`)

```python
SYSTEM_PROMPT = """
You are a facts-only mutual fund FAQ assistant for HDFC schemes.

STRICT RULES:
1. Answer ONLY using the CONTEXT provided below. Never infer or hallucinate.
2. Your answer must be at most 3 sentences.
3. End your answer with: Source: <source_url>
4. End your answer with footer: Last updated from sources: <date>
5. NEVER give investment advice, fund recommendations, or return predictions.
6. If the answer is not in the CONTEXT, respond:
   "I could not find this information in official sources. Please visit <source_url>."
"""

def build_prompt(query: str, chunks: list[dict]) -> str:
    context = "\n\n".join(c["text"] for c in chunks)
    source_url = chunks[0]["source_url"] if chunks else "https://www.amfiindia.com"
    date = chunks[0]["date"] if chunks else "N/A"
    return f"""{SYSTEM_PROMPT}

CONTEXT:
{context}

USER QUERY: {query}
SOURCE: {source_url}
DATE: {date}
"""
```

### 4.4 LLM Client (`pipeline/llm_client.py`)

Uses the **Groq API** with `openai/gpt-oss-120b` — an OpenAI-compatible model on Groq's LPU hardware.

#### Rate Limits (free tier)

| Limit | Value | Impact |
|---|---|---|
| Requests per minute | **30 RPM** | ~1 req / 2 sec max |
| Requests per day | **1 K** | ~41/hr if spread evenly |
| Tokens per minute | **8 K TPM** | ~4–6 calls/min at full context |
| Tokens per day | **200 K** | ~200 full calls/day |

#### Three mitigations implemented

**1. LRU Response Cache** (`functools.lru_cache`, 256 slots)
Identical queries return a cached answer instantly — zero tokens consumed, zero requests used.
```python
@lru_cache(maxsize=LLM_CACHE_SIZE)   # LLM_CACHE_SIZE = 256
def _cached_call(prompt_hash: str, prompt: str) -> str: ...
```

**2. Retry with Exponential Backoff**
On `groq.RateLimitError` (429): sleep 2 s → 4 s → 8 s, then raise.
```python
LLM_MAX_RETRIES      = 3
LLM_RETRY_BASE_DELAY = 2.0   # doubles each retry
```

**3. Token Budget Discipline**
- `max_tokens = 200` (down from 300) — 3 sentences needs ~100 tokens
- Each chunk trimmed to `CHUNK_CONTEXT_CHARS = 600` chars (~150 tokens)
- 4 chunks × 150 ≈ 600 context tokens + ~150 system prompt = **~950 tokens/call**
- Headroom: 8 K TPM ÷ 950 ≈ **8 calls/minute safely**

**Why Groq?**

| Property | Value |
|---|---|
| Inference speed | ~500 tokens/sec (LPU hardware) |
| Model | `openai/gpt-oss-120b` — OpenAI-compatible, strong instruction-following |
| Previous model | `llama-3.3-70b-versatile` (decommissioned) |
| Temperature | `0.0` — fully deterministic, no hallucination drift |
| Max tokens | `200` — enforces short, factual answers |
| Cache | LRU 256 slots — repeat queries cost 0 tokens |
| Retry | 3× exponential backoff on 429 (2 s → 4 s → 8 s) |
| API key | Set `GROQ_API_KEY` in `.env` — get from https://console.groq.com |

### 4.5 Response Formatter (`pipeline/response_formatter.py`)

Post-processes every LLM output:

```python
import re, datetime

def format_response(raw: str, source_url: str, date: str) -> str:
    # 1. Trim to max 3 sentences
    sentences = re.split(r'(?<=[.?!])\s+', raw.strip())
    trimmed = " ".join(sentences[:3])

    # 2. Ensure citation present
    if "Source:" not in trimmed:
        trimmed += f"\nSource: {source_url}"

    # 3. Ensure date footer
    if "Last updated" not in trimmed:
        trimmed += f"\nLast updated from sources: {date}"

    # 4. Append disclaimer
    trimmed += "\n\n> Facts-only. No investment advice."
    return trimmed
```

### 4.6 Refusal Handler (`pipeline/refusal_handler.py`)

```python
REFUSAL_TEMPLATE = """I'm designed to answer only factual questions about \
HDFC mutual fund schemes (e.g., expense ratios, exit loads, SIP amounts, lock-in periods).

I'm unable to provide investment advice, recommendations, or performance comparisons.
For investor education, please visit: https://www.amfiindia.com/investor-corner

> Facts-only. No investment advice."""

PII_TEMPLATE = """For your privacy and security, I cannot process queries that contain \
personal identifiers such as PAN, Aadhaar, account numbers, or contact details.
Please rephrase your question without personal information.

> Facts-only. No investment advice."""

def get_refusal(reason: str) -> str:
    return PII_TEMPLATE if reason == "pii" else REFUSAL_TEMPLATE
```

### 4.7 Main Pipeline Orchestrator (`pipeline/main.py`)

```python
from pipeline.classifier    import classify
from retrieval.retriever    import retrieve
from pipeline.prompt_builder import build_prompt
from pipeline.llm_client    import call_llm
from pipeline.response_formatter import format_response
from pipeline.refusal_handler import get_refusal

def answer(query: str) -> str:
    intent = classify(query)

    if intent in ("advisory", "pii"):
        return get_refusal(intent)

    chunks = retrieve(query)
    if not chunks:
        return ("I could not find this information in the official sources. "
                "Please visit https://www.amfiindia.com for more details.\n\n"
                "> Facts-only. No investment advice.")

    prompt  = build_prompt(query, chunks)
    raw     = call_llm(prompt)
    return format_response(raw, chunks[0]["source_url"], chunks[0]["date"])
```

### ✅ Phase 4 Deliverable
- `answer("What is the exit load of HDFC ELSS?")` returns a correct, 3-sentence, cited response
- `answer("Should I invest in HDFC Mid Cap?")` returns the polite refusal
- `answer("My PAN is ABCDE1234F")` returns the PII refusal
- All module imports resolve without errors

---

## Phase 5 — Frontend UI

**Goal:** Build a premium, production-quality chat interface by porting the **Google Stitch** exported design into a **Next.js 14** React application, backed by a **FastAPI** Python API that exposes the RAG pipeline. The Streamlit `ui/app.py` is preserved as a lightweight fallback.

> [!NOTE]
> **Production deployment:** Frontend is deployed on **Vercel**, backend on **Railway**. See [deployment-plan.md](deployment-plan.md) for the full deployment guide.

> [!IMPORTANT]
> **Stitch design already exported.** The Google Stitch design output lives at `ui/static/stitch_hdfc_fund_fact_assistant/`. It includes `code.html` (full TailwindCSS prototype), the **Lumina Finance** design system (`DESIGN.md`), and preview screenshots. The Next.js app will faithfully port this HTML into typed React components.

### 5.1 UI Requirements (from problem statement)

| Element | Specification |
|---|---|
| Welcome message | Brief description of the assistant's purpose |
| Example questions | 3 clickable pre-filled queries |
| Chat interface | Query input + response display |
| Disclaimer | Persistent banner: `"Facts-only. No investment advice."` |
| Source footer | Rendered below every answer |

### 5.2 Stitch Export — Source Files

The Stitch design has been **already generated and exported** to:

```
ui/static/stitch_hdfc_fund_fact_assistant/
└── stitch_hdfc_fund_fact_assistant/
    ├── mutual_fund_assistant_chat/
    │   ├── code.html       ← Complete UI prototype (TailwindCSS + Plus Jakarta Sans)
    │   └── screen.png      ← Design preview screenshot
    ├── lumina_finance/
    │   └── DESIGN.md       ← Full design system specification (colors, typography, spacing)
    └── hdfc_assistant_logo/
        └── screen.png      ← Logo asset
```

**`code.html` implements:**
- Fixed sidebar with 5 HDFC scheme entries + risk badges (Very High / High / Moderate)
- Glassmorphism header with logo, title, and disclaimer pill
- Welcome/empty state with animated hero icon and 3 example question cards
- Chat bubble layout (user = right teal, bot = left glassmorphism card)
- Source citation chips + "Last updated" footer on bot messages
- Typing indicator with 3-dot bounce animation
- Fixed floating input bar at bottom (rounded-full, backdrop-blur)
- `fade-in-up`, `fade-in-left`, `fade-in-right` entry animations

**Lumina Finance design system (from `DESIGN.md`):**

| Token | Value |
|---|---|
| Background | `#0b1326` (midnight navy) |
| Primary (teal) | `#89ceff` / `#0ea5e9` |
| Secondary (gold) | `#ffb95f` / `#ee9800` |
| Surface container | `#171f33` |
| Typography | Plus Jakarta Sans (all weights) |
| Base radius | 16px bubbles, full-pill for badges/chips |
| Spacing unit | 4px grid |
| Glassmorphism | `backdrop-blur-xl`, `bg-surface-container/60`, `border-white/10` |

### 5.3 Next.js Frontend App (`frontend/`)

Port the Stitch `code.html` into a **Next.js 14** app (App Router) with **TailwindCSS**. Next.js is chosen for:
- Server-side rendering for faster first load
- TypeScript support for type-safe API calls
- Built-in routing (future multi-page expansion)
- Production build optimisation (`next build`)

#### 5.3.1 Project Scaffold

```bash
# Run from the ragchatbot/ project root
npx -y create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --no-git
```

#### 5.3.2 Folder Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx          ← Root layout: Plus Jakarta Sans font, dark bg, metadata
│   │   ├── page.tsx            ← Main chat page (renders ChatApp)
│   │   ├── globals.css         ← Lumina Finance CSS variables + Tailwind base
│   │   └── api/
│   │       └── chat/
│   │           └── route.ts    ← Next.js API route that proxies to FastAPI
│   ├── components/
│   │   ├── Sidebar.tsx         ← Scheme list with risk badges
│   │   ├── Header.tsx          ← Logo + title + disclaimer pill
│   │   ├── EmptyState.tsx      ← Welcome hero + 3 example cards
│   │   ├── ChatHistory.tsx     ← Message list with scroll-to-bottom
│   │   ├── UserBubble.tsx      ← Right-aligned teal bubble
│   │   ├── BotBubble.tsx       ← Left-aligned glass card + source chip
│   │   ├── TypingIndicator.tsx ← 3-dot bounce animation
│   │   └── InputBar.tsx        ← Fixed bottom input + send button
│   ├── hooks/
│   │   └── useChat.ts          ← Chat state, API call, message management
│   └── types/
│       └── chat.ts             ← Message, QueryRequest, QueryResponse types
├── tailwind.config.ts          ← Lumina Finance color tokens + font config
├── next.config.js              ← API proxy to FastAPI backend
└── package.json
```

#### 5.3.3 Tailwind Config — Lumina Finance Tokens

Extend `tailwind.config.ts` to match the Stitch design system exactly:

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background:               "#0b1326",
        "surface":                "#0b1326",
        "surface-container":      "#171f33",
        "surface-container-high": "#222a3d",
        "surface-variant":        "#2d3449",
        "on-surface":             "#dae2fd",
        "on-surface-variant":     "#bec8d2",
        "primary":                "#89ceff",
        "primary-container":      "#0ea5e9",
        "on-primary":             "#00344d",
        "secondary":              "#ffb95f",
        "secondary-container":    "#ee9800",
        "tertiary":               "#ffb86e",
        "tertiary-container":     "#de8712",
        "outline-variant":        "#3e4850",
        "error":                  "#ffb4ab",
        "error-container":        "#93000a",
      },
      fontFamily: {
        sans: ["Plus Jakarta Sans", "sans-serif"],
      },
      borderRadius: {
        "2xl": "1.25rem",
        "3xl": "1.5rem",
      },
      keyframes: {
        "fade-in-up":    { "0%": { opacity:"0", transform:"translateY(30px)" },  "100%": { opacity:"1", transform:"translateY(0)" } },
        "fade-in-left":  { "0%": { opacity:"0", transform:"translateX(-30px)" }, "100%": { opacity:"1", transform:"translateX(0)" } },
        "fade-in-right": { "0%": { opacity:"0", transform:"translateX(30px)" },  "100%": { opacity:"1", transform:"translateX(0)" } },
        "bounce-dot":    { "0%,100%": { transform:"translateY(0)" }, "50%": { transform:"translateY(-6px)" } },
      },
      animation: {
        "fade-in-up":   "fade-in-up 0.8s ease-out forwards",
        "fade-in-left": "fade-in-left 0.4s ease-out forwards",
        "fade-in-right":"fade-in-right 0.4s ease-out forwards",
        "bounce-dot-1": "bounce-dot 1s infinite 0ms",
        "bounce-dot-2": "bounce-dot 1s infinite 200ms",
        "bounce-dot-3": "bounce-dot 1s infinite 400ms",
      },
    },
  },
  plugins: [],
};
export default config;
```

#### 5.3.4 Chat State Hook (`useChat.ts`)

```typescript
// src/hooks/useChat.ts
import { useState, useCallback } from "react";

export interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const send = useCallback(async (query: string) => {
    const userMsg: Message = {
      role: "user",
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, {
        role: "assistant",
        content: data.response,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Service unavailable. Please try again later.",
        timestamp: "",
      }]);
    } finally {
      setLoading(false);
    }
  }, []);

  return { messages, loading, send };
}
```

#### 5.3.5 Next.js API Route Proxy

```typescript
// src/app/api/chat/route.ts
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const response = await fetch("http://localhost:8000/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  return NextResponse.json(data);
}
```

### 5.4 FastAPI Backend (`ui/api.py`)

Exposes the Python RAG pipeline as a JSON REST API with CORS enabled for the Next.js dev server:

```python
# ui/api.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.main import answer

app = FastAPI(title="HDFC Fund FAQ API")

# CORS: include Vercel production URL from env var (set in Railway dashboard)
_ALLOWED_ORIGINS = [
    "http://localhost:3000",   # Next.js dev
    "http://localhost:8000",   # FastAPI health check
]
_vercel_url = os.getenv("FRONTEND_URL")
if _vercel_url:
    _ALLOWED_ORIGINS.append(_vercel_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

@app.get("/health")
async def health():
    return {"status": "ok", "service": "HDFC Fund FAQ API"}

@app.post("/api/chat", response_model=QueryResponse)
async def chat(req: QueryRequest):
    return QueryResponse(response=answer(req.query))
```

### 5.5 Updated Dependencies

**Python (`requirements.txt`) — add:**
```
fastapi
uvicorn[standard]
```

**Node.js — auto-installed by `create-next-app`:**
```json
{
  "next": "^14",
  "react": "^18",
  "react-dom": "^18",
  "tailwindcss": "^3",
  "typescript": "^5"
}
```

### 5.6 Run the Full Stack

**Step 1 — Start the FastAPI backend:**
```bash
uvicorn ui.api:app --reload --port 8000
```

**Step 2 — Start the Next.js frontend:**
```bash
cd frontend
npm install        # first time only
npm run dev
# → Open http://localhost:3000
```

**Step 3 — Fallback (Streamlit only):**
```bash
streamlit run ui/app.py
# → Open http://localhost:8501
```

### 5.7 Streamlit Fallback (`ui/app.py`)

The existing Streamlit implementation is preserved as-is for rapid testing and as a fallback. No changes needed — it continues to work via `streamlit run ui/app.py`.

### ✅ Phase 5 Deliverable
- Stitch design exported and referenced from `ui/static/stitch_hdfc_fund_fact_assistant/`
- Next.js app scaffolded in `frontend/` with Lumina Finance Tailwind tokens
- All Stitch components ported as typed React components
- FastAPI backend live at `http://localhost:8000/api/chat`
- Next.js frontend live at `http://localhost:3000`
- Premium dark-mode chat UI: glassmorphism bubbles, scheme sidebar, micro-animations
- Source citation chips, "Last updated" footer, and disclaimer pill rendered correctly
- Mobile responsive (sidebar collapses on small screens)
- Streamlit fallback still functional at `http://localhost:8501`

---

## Phase 6 — Testing, Hardening & Documentation

**Goal:** Validate all success criteria from the problem statement, harden edge cases, and finalize documentation.

### 6.1 Test Suite (`tests/`)

| Test File | What It Tests |
|---|---|
| `test_classifier.py` | Advisory, PII, and factual queries correctly classified |
| `test_retriever.py` | Top-K results returned for known factual queries |
| `test_formatter.py` | Response ≤ 3 sentences, citation present, footer present |
| `test_refusal.py` | All advisory trigger phrases return refusal response |
| `test_pipeline.py` | End-to-end: factual query returns correct answer with source |
| `test_pii.py` | PAN/Aadhaar patterns trigger PII refusal |

**Sample test cases:**

| Query | Expected Behaviour |
|---|---|
| `"What is the expense ratio of HDFC Mid Cap Fund?"` | Factual answer ≤ 3 sentences + source URL + date |
| `"What is the lock-in period of HDFC ELSS?"` | Answer: 3 years + ELSS source |
| `"What is the minimum SIP for HDFC Large Cap?"` | Correct SIP amount retrieved |
| `"Should I invest in HDFC Gold FoF?"` | Refusal + AMFI link |
| `"Which fund has the best returns?"` | Refusal + AMFI link |
| `"My PAN is ABCDE1234F"` | PII refusal |
| `"What is the NAV today?"` | Factsheet link only (no live NAV) |
| `"What is the riskometer of HDFC Small Cap?"` | Risk level from factsheet |

### 6.2 Compliance Checklist

Before final delivery, verify every item:

- [ ] All responses ≤ 3 sentences
- [ ] All responses include exactly 1 source URL
- [ ] All responses include `"Last updated from sources: <date>"` footer
- [ ] Advisory queries refused with AMFI/SEBI link
- [ ] PII queries rejected with privacy notice
- [ ] No third-party blog or aggregator domain in any source URL
- [ ] No PII stored or logged anywhere in the application
- [ ] Disclaimer `"Facts-only. No investment advice."` appears on every UI page and every response
- [ ] Performance comparison queries refused
- [ ] Return prediction queries refused

### 6.3 Known Edge Cases to Handle

| Edge Case | Handling |
|---|---|
| Query about a non-HDFC scheme | "This assistant only covers HDFC schemes. Please visit [AMC page]." |
| Empty retrieval (low similarity) | "I could not find this in official sources. Visit [URL]." |
| LLM exceeds 3 sentences | Response formatter truncates at sentence 3 |
| LLM omits citation | Formatter injects top retrieved chunk's source URL |
| Scraper fails (site down) | Log warning; use last cached data; note stale date in footer |

### 6.4 README (`README.md`)

Include:
- Project overview and disclaimer
- Selected AMC (HDFC) and 5 scheme URLs
- Architecture overview (link to `architecture.md`)
- Setup instructions (clone → install → configure `.env` → ingest → run UI)
- How to re-run ingestion
- Known limitations (from `architecture.md §8`)

### ✅ Phase 6 Deliverable
- All test cases in `tests/` pass
- Compliance checklist fully signed off
- `README.md` complete with setup, architecture link, and limitations
- Application demo-ready

---

## Phase 7 — Daily Scheduler & Auto-Update Pipeline (GitHub Actions)

**Goal:** Automatically run the full scrape → chunk → embed → ChromaDB refresh cycle every day using **GitHub Actions**, so the RAG knowledge base always reflects the latest NAV, expense ratios, and fund facts from Groww — with zero infrastructure cost and full run history in the GitHub UI.

> [!IMPORTANT]
> The update is **incremental**: per-scheme chunks are deleted from ChromaDB and re-inserted with fresh data. The workflow uploads the updated `data/metadata.json` and `vector_store/` as a GitHub Actions artifact **and** commits `metadata.json` back to the repo so Railway/Vercel always knows the last successful scrape date.

### 7.1 Folder & File Changes

```
ragchatbot/
├── .github/
│   └── workflows/
│       ├── daily_update.yml      ← [NEW] Daily cron + manual trigger
│       └── manual_ingest.yml     ← [NEW] On-demand single-scheme re-ingest
├── scheduler/
│   └── daily_update.py           ← Incremental ChromaDB refresh (reused by GH Actions)
├── ingest_all.py                  ← Entry point called by the workflow
└── data/
    └── metadata.json             ← Committed back after each run
```

### 7.2 Daily Update Orchestrator (`scheduler/daily_update.py`)

This module is called by `ingest_all.py` and reuses the existing ingestion stack. It performs an incremental per-scheme refresh:

```python
# scheduler/daily_update.py
import logging
import datetime
import json
from pathlib import Path

import chromadb
from ingestion.scraper  import scrape_scheme
from ingestion.chunker  import chunk_document
from ingestion.embedder import ingest_chunks
from config import SCHEME_URLS, CHROMA_DB_PATH

logger = logging.getLogger("scheduler")
METADATA_PATH = Path("data/metadata.json")


def _scheme_slug(url: str) -> str:
    """Derive a stable slug from the Groww URL tail segment."""
    return url.rstrip("/").split("/")[-1]


def _delete_scheme_chunks(collection, scheme_slug: str):
    """Delete stale ChromaDB documents for this scheme before re-ingesting."""
    existing = collection.get(where={"source_url": {"$contains": scheme_slug}})
    if existing["ids"]:
        collection.delete(ids=existing["ids"])
        logger.info("Deleted %d stale chunks for %s", len(existing["ids"]), scheme_slug)


def run_daily_update(urls: list[str] | None = None) -> dict:
    """
    Orchestrates the full daily refresh for the given URLs (default: all SCHEME_URLS):
      1. Scrape each scheme URL from Groww
      2. Chunk and classify the fresh content
      3. Delete stale ChromaDB entries for that scheme
      4. Embed and insert fresh chunks
      5. Update metadata.json with new scrape_date and chunk_count
    Returns a summary dict printed to stdout (captured by GitHub Actions logs).
    """
    urls = urls or SCHEME_URLS
    client     = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection("mutual_fund_facts")
    summary    = {"run_date": datetime.date.today().isoformat(), "schemes": {}}
    metadata   = json.loads(METADATA_PATH.read_text()) if METADATA_PATH.exists() else {}

    for url in urls:
        slug = _scheme_slug(url)
        logger.info("[%s] Starting scrape …", slug)
        try:
            scraped = scrape_scheme(url)
            chunks  = chunk_document(
                text=scraped["content"],
                source_url=url,
                scrape_date=scraped["scraped_at"],
                scheme_name=scraped["scheme_name"],
            )
            _delete_scheme_chunks(collection, slug)
            ingest_chunks(chunks, scheme_slug=slug)

            non_noise = [c for c in chunks if c["chunk_type"] != "noise"]
            metadata[slug] = {
                "source_url":   url,
                "scrape_date":  scraped["scraped_at"],
                "chunk_count":  len(non_noise),
                "type":         "web",
                "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
            }
            summary["schemes"][slug] = {"status": "ok", "chunks": len(non_noise)}
            logger.info("[%s] ✅  Ingested %d chunks.", slug, len(non_noise))

        except Exception as exc:
            logger.error("[%s] ❌  Failed: %s", slug, exc, exc_info=True)
            summary["schemes"][slug] = {"status": "error", "error": str(exc)}

    METADATA_PATH.write_text(json.dumps(metadata, indent=2))
    logger.info("Daily update complete: %s", summary)
    return summary
```

### 7.3 Primary Scheduler — GitHub Actions Workflow

#### 7.3.1 Daily Cron Workflow (`.github/workflows/daily_update.yml`)

> [!IMPORTANT]
> This is the **primary, recommended** scheduler. It runs on GitHub's hosted runners at 02:00 UTC daily (07:30 IST). No server or APScheduler process needed. Run history, logs, and artifacts are all visible in the GitHub Actions tab.

```yaml
name: 🔄 Daily Fund Data Refresh

on:
  # ── Automatic: every day at 02:00 UTC (07:30 IST) ──────────────────────────
  schedule:
    - cron: "0 2 * * *"

  # ── Manual: trigger from GitHub UI or via API ───────────────────────────────
  workflow_dispatch:
    inputs:
      scheme_url:
        description: |
          (Optional) Re-ingest a single scheme URL.
          Leave blank to refresh ALL 5 HDFC schemes.
        required: false
        default: ""
      dry_run:
        description: "Dry run — scrape only, do NOT update ChromaDB or commit"
        type: boolean
        required: false
        default: false

jobs:
  # ============================================================
  # JOB 1 — Run the ingestion pipeline
  # ============================================================
  daily-update:
    name: Scrape → Embed → Refresh ChromaDB
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      # ── 1. Checkout repo (with full history for git push) ──────────────────
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0          # full history so we can push back
          token: ${{ secrets.GITHUB_TOKEN }}

      # ── 2. Set up Python ───────────────────────────────────────────────────
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"            # cache site-packages between runs

      # ── 3. Install dependencies ────────────────────────────────────────────
      - name: Install dependencies
        run: pip install -r requirements.txt

      # ── 4. Restore cached ChromaDB from previous run ───────────────────────
      - name: Restore ChromaDB cache
        uses: actions/cache@v4
        with:
          path: vector_store/chroma_db
          key: chroma-db-${{ runner.os }}-${{ hashFiles('data/metadata.json') }}
          restore-keys: |
            chroma-db-${{ runner.os }}-

      # ── 5. Run ingestion ───────────────────────────────────────────────────
      - name: Run daily ingestion
        env:
          GROQ_API_KEY:  ${{ secrets.GROQ_API_KEY }}
          SCHEME_URL:    ${{ github.event.inputs.scheme_url }}
          DRY_RUN:       ${{ github.event.inputs.dry_run }}
        run: |
          python ingest_all.py \
            ${SCHEME_URL:+--url "$SCHEME_URL"} \
            ${DRY_RUN:+--dry-run}

      # ── 6. Upload ChromaDB + metadata as artifact ──────────────────────────
      - name: Upload vector store artifact
        if: ${{ github.event.inputs.dry_run != 'true' }}
        uses: actions/upload-artifact@v4
        with:
          name: chroma-db-${{ github.run_number }}
          path: |
            vector_store/chroma_db/
            data/metadata.json
          retention-days: 7       # keep the last 7 daily snapshots

      # ── 7. Commit updated metadata.json back to repo ───────────────────────
      - name: Commit metadata update
        if: ${{ github.event.inputs.dry_run != 'true' }}
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/metadata.json
          git diff --cached --quiet || git commit \
            -m "chore(scheduler): daily fund data refresh $(date -u +%Y-%m-%d) [skip ci]"
          git push

      # ── 8. Write GitHub Step Summary ───────────────────────────────────────
      - name: Write job summary
        if: always()
        run: |
          python - <<'EOF'
          import json, os
          from pathlib import Path
          meta = json.loads(Path("data/metadata.json").read_text())
          lines = ["## 📊 Daily Fund Refresh Summary\n",
                   "| Scheme | Status | Chunks | Scrape Date |",
                   "|---|---|---|---|"]
          for slug, info in meta.items():
              status = "✅" if info.get("scrape_date") else "❌"
              lines.append(
                f"| {slug} | {status} | {info.get('chunk_count','?')} | {info.get('scrape_date','N/A')} |"
              )
          summary_path = os.environ["GITHUB_STEP_SUMMARY"]
          Path(summary_path).write_text("\n".join(lines))
          EOF

  # ============================================================
  # JOB 2 — Notify on failure (runs only when job 1 fails)
  # ============================================================
  notify-on-failure:
    name: Notify on failure
    runs-on: ubuntu-latest
    needs: daily-update
    if: failure()
    steps:
      - name: Send failure notification
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo:  context.repo.repo,
              title: `❌ Daily fund refresh failed — ${new Date().toISOString().slice(0,10)}`,
              body:  `The scheduled daily ChromaDB refresh failed.\n\n**Workflow run:** ${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}`,
              labels: ["bug", "scheduler"],
            });
```

#### 7.3.2 Manual Single-Scheme Workflow (`.github/workflows/manual_ingest.yml`)

Use this to re-ingest a specific scheme on demand (e.g., after a Groww page layout change):

```yaml
name: ♻️ Manual Single-Scheme Re-Ingest

on:
  workflow_dispatch:
    inputs:
      scheme_url:
        description: "Full Groww scheme URL to re-ingest"
        required: true
        default: "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"

jobs:
  reingest:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - run: pip install -r requirements.txt

      - name: Restore ChromaDB cache
        uses: actions/cache@v4
        with:
          path: vector_store/chroma_db
          key: chroma-db-${{ runner.os }}-${{ hashFiles('data/metadata.json') }}
          restore-keys: chroma-db-${{ runner.os }}-

      - name: Re-ingest single scheme
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
        run: python ingest_all.py --url "${{ github.event.inputs.scheme_url }}"

      - name: Commit metadata
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/metadata.json
          git diff --cached --quiet || git commit \
            -m "chore(scheduler): manual re-ingest ${{ github.event.inputs.scheme_url }} [skip ci]"
          git push
```

### 7.4 `ingest_all.py` — CLI Entry Point

Update `ingest_all.py` to accept `--url` and `--dry-run` flags so the GitHub Actions workflow can target a single scheme or skip writes:

```python
# ingest_all.py
import argparse
import logging
from scheduler.daily_update import run_daily_update
from config import SCHEME_URLS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def main():
    parser = argparse.ArgumentParser(description="HDFC Fund data ingestion pipeline")
    parser.add_argument(
        "--url", default="",
        help="Re-ingest a single scheme URL. Omit to refresh all schemes."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Scrape and chunk only — do not write to ChromaDB or metadata.json."
    )
    args = parser.parse_args()

    urls = [args.url] if args.url else SCHEME_URLS
    if args.dry_run:
        logging.info("DRY RUN — no ChromaDB writes.")
        # just scrape and print chunk counts
        from ingestion.scraper import scrape_scheme
        from ingestion.chunker import chunk_document
        for url in urls:
            scraped = scrape_scheme(url)
            chunks  = chunk_document(
                text=scraped["content"],
                source_url=url,
                scrape_date=scraped["scraped_at"],
                scheme_name=scraped["scheme_name"],
            )
            non_noise = [c for c in chunks if c["chunk_type"] != "noise"]
            logging.info("%s → %d non-noise chunks (dry run)", url, len(non_noise))
    else:
        run_daily_update(urls=urls)

if __name__ == "__main__":
    main()
```

### 7.5 GitHub Repository Secrets Required

Before the workflow can run, add these secrets in **GitHub → Settings → Secrets → Actions**:

| Secret | Value | Where used |
|---|---|---|
| `GROQ_API_KEY` | Your Groq API key | `ingest_all.py` LLM calls (if any during ingest) |

> [!NOTE]
> `GITHUB_TOKEN` is automatically provided by GitHub Actions — no manual setup needed for the commit-back step.

### 7.6 ChromaDB Persistence Strategy

GitHub Actions runners are ephemeral — the ChromaDB is rebuilt on every run using `actions/cache`:

| Step | Mechanism | Detail |
|---|---|---|
| **Restore** | `actions/cache@v4` | Restores prior `vector_store/chroma_db/` from cache keyed on `metadata.json` hash |
| **Update** | `scheduler/daily_update.py` | Incremental — deletes stale chunks, inserts fresh ones |
| **Persist** | `actions/upload-artifact@v4` | 7-day artifact snapshot of the full ChromaDB after each run |
| **Railway sync** | Railway deploy hook (optional) | After a successful run, trigger a Railway redeploy to pick up the latest `metadata.json` from git |

> [!WARNING]
> Do **not** commit `vector_store/chroma_db/` binary files to git — they can grow large. The artifact upload handles snapshots. The cache + incremental approach keeps runner times under 5 minutes per run.

### 7.7 Stale-Data Guard (Runtime Awareness)

The RAG pipeline warns users in-chat when it is serving data older than `STALE_DATA_THRESHOLD_DAYS`. Add a helper in `pipeline/response_formatter.py`:

```python
import datetime
from config import STALE_DATA_THRESHOLD_DAYS

def _is_stale(date_str: str) -> bool:
    """Return True if scrape_date is more than STALE_DATA_THRESHOLD_DAYS old."""
    try:
        return (datetime.date.today() - datetime.date.fromisoformat(date_str)).days \
               > STALE_DATA_THRESHOLD_DAYS
    except (ValueError, TypeError):
        return False

def format_response(raw: str, source_url: str, date: str) -> str:
    # ... existing formatting logic ...
    if _is_stale(date):
        trimmed += "\n> ⚠️ Data may be outdated — next automatic GitHub Actions refresh scheduled tonight."
    trimmed += "\n\n> Facts-only. No investment advice."
    return trimmed
```

`STALE_DATA_THRESHOLD_DAYS` is set in `config.py`:

```python
STALE_DATA_THRESHOLD_DAYS = int(os.getenv("STALE_DATA_THRESHOLD_DAYS", "2"))
```

### 7.8 Local Fallback (Dev Only)

For local development without GitHub Actions, run ingestion directly:

```bash
# Refresh all 5 schemes (ad-hoc)
python ingest_all.py

# Refresh a single scheme
python ingest_all.py --url "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth"

# Dry-run — scrape only, no ChromaDB writes
python ingest_all.py --dry-run
```

Alternatively, use Windows Task Scheduler for local automation:
```powershell
schtasks /create /tn "HDFCFundDailyUpdate" /tr "python G:\Ragchatbot\ingest_all.py" /sc daily /st 09:00 /f
```

### 7.9 Monitoring & Observability

| What | Where | How to access |
|---|---|---|
| Run history & logs | GitHub → Actions tab | Every cron and manual run listed with full logs |
| Step summary table | GitHub Actions run page → Summary | Per-scheme ✅/❌ status + chunk counts |
| ChromaDB snapshot | GitHub Actions → Artifacts | Last 7 daily snapshots downloadable |
| `metadata.json` | Committed to repo after each run | `git log -- data/metadata.json` shows history |
| Failure alert | Auto-created GitHub Issue (labelled `bug`, `scheduler`) | Assigned to repo collaborators |
| Stale-data warning | In-chat UI (response footer) | Visible to end users after 2 missed runs |

### ✅ Phase 7 Deliverable
- `.github/workflows/daily_update.yml` committed and **enabled** in GitHub Actions
- `.github/workflows/manual_ingest.yml` committed for on-demand re-ingest
- `GROQ_API_KEY` secret added to GitHub repository settings
- First manual `workflow_dispatch` run completes successfully (all 5 schemes ✅)
- `data/metadata.json` `scrape_date` fields updated after the run
- GitHub Step Summary shows per-scheme table for every run
- ChromaDB artifact uploaded and retained for 7 days
- Stale-data warning verified in UI when `scrape_date` is > 2 days old
- Failure auto-issue creation tested by temporarily breaking one scheme URL

---

## Summary Timeline

| Phase | Focus Area | Duration | Deliverable |
|---|---|---|---|
| **1** | Environment & Scaffold | Day 1 | Working project structure + config |
| **2** | Data Ingestion | Day 2–3 | Scraped + chunked documents in `data/` |
| **3** | Embedding & Vector Store | Day 4 | Populated ChromaDB, test retrieval working |
| **4** | RAG Query Pipeline | Day 5–6 | End-to-end `answer()` function working |
| **5** | Frontend UI (Next.js + FastAPI) | Day 7–8 | Next.js app at localhost:3000 → FastAPI at localhost:8000 |
| **6** | Testing & Documentation | Day 8–9 | All tests pass, README complete |
| **7** | Daily Scheduler (GitHub Actions) | Day 10 | Workflows live, daily cron firing, ChromaDB auto-refreshed |
| **8** | Production Deployment | Day 11 | Railway backend + worker live, Vercel frontend live (see [deployment-plan.md](deployment-plan.md)) |

---

## Success Criteria Mapping

| Problem Statement Criterion | Implementation Coverage |
|---|---|
| Accurate retrieval of factual info | Phase 3 (ChromaDB) + Phase 4 (Retriever) |
| Strict facts-only responses | Phase 4 (System prompt + Formatter) |
| Valid source citation in every response | Phase 4 (Formatter §4.5) |
| Proper refusal of advisory queries | Phase 4 (Classifier §4.1 + Refusal Handler §4.6) |
| Clean, minimal, user-friendly UI | Phase 5 (Stitch design §5.2 → Next.js §5.3 + FastAPI §5.4) |
| Always-fresh data (daily NAV / expense ratio updates) | Phase 7 (GitHub Actions cron §7.3.1 + Incremental ChromaDB update §7.2) |
| On-demand single-scheme re-ingest | Phase 7 (manual_ingest.yml §7.3.2 + `ingest_all.py --url`) |
| Stale-data transparency | Phase 7 (Stale-data guard §7.7 rendered in every response) |

---

> **Disclaimer:** Facts-only. No investment advice.

