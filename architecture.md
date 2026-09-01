# Architecture: Mutual Fund FAQ Assistant (RAG-Based)

> **Disclaimer:** Facts-only. No investment advice.

---

## 1. System Overview

The Mutual Fund FAQ Assistant is a **Retrieval-Augmented Generation (RAG)** pipeline that answers factual, verifiable questions about HDFC mutual fund schemes. It combines a curated vector knowledge base of official documents with a language model that is strictly prompted to produce short, source-cited, facts-only responses.

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (UI Layer)                    │
│  Welcome message · 3 example questions · Disclaimer banner  │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     BACKEND (API Layer)                     │
│  Query Classifier → Retriever → Prompt Builder → LLM → Response Formatter │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  KNOWLEDGE BASE (Vector Store)              │
│  Chunked & embedded documents from AMC · AMFI · SEBI        │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                          DATA INGESTION PIPELINE                     │
│                                                                      │
│  [Groww / AMC Pages]  [AMFI Data]  [SEBI Circulars]                 │
│         │                  │               │                         │
│         └──────────────────┴───────────────┘                        │
│                            │                                         │
│                    [Web Scraper / PDF Parser]                        │
│                            │                                         │
│                    [Text Cleaner & Chunker]                          │
│                            │                                         │
│                    [Embedding Model]                                 │
│                            │                                         │
│                    [Vector Store (ChromaDB / FAISS)]                 │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                          QUERY PIPELINE (Runtime)                   │
│                                                                      │
│  User Query                                                          │
│      │                                                               │
│      ▼                                                               │
│  [Query Classifier]                                                  │
│      │                                                               │
│      ├── Advisory/Refusal → [Refusal Handler] → Polite Refusal      │
│      │                                           + AMFI/SEBI Link    │
│      │                                                               │
│      └── Factual Query                                               │
│              │                                                       │
│              ▼                                                       │
│      [Query Embedder]                                                │
│              │                                                       │
│              ▼                                                       │
│      [Vector Store Retriever] ── Top-K chunks (k=3-5)               │
│              │                                                       │
│              ▼                                                       │
│      [Prompt Builder]                                                │
│        System prompt + retrieved context + user query               │
│              │                                                       │
│              ▼                                                       │
│      [LLM (Groq – llama-3.3-70b-versatile)]                         │
│              │                                                       │
│              ▼                                                       │
│      [Response Formatter]                                            │
│        ≤ 3 sentences · 1 citation · date footer                     │
│              │                                                       │
│              ▼                                                       │
│      Final Response → Frontend                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Breakdown

### 3.1 Data Ingestion Pipeline

The knowledge base is built **exclusively** from the 5 Groww scheme pages listed in the corpus. No PDFs, no AMFI downloads, no SEBI documents — Groww aggregates all the required factual data (expense ratio, exit load, SIP minimum, riskometer, benchmark, lock-in period) on each scheme page.

| Component | Technology | Purpose |
|---|---|---|
| Web Scraper | `BeautifulSoup4` + `Requests` | Scrapes all 5 Groww scheme pages for factual data |
| Text Cleaner | Custom regex pipeline | Removes navigation boilerplate, normalises whitespace |
| Chunker | `LangChain RecursiveCharacterTextSplitter` | Splits text into 300–500 token chunks with overlap |
| Embedding Model | `all-MiniLM-L6-v2` (local, HuggingFace) | Converts chunks to dense vectors |
| Vector Store | `ChromaDB` (local) | Stores and indexes embedded chunks |
| Metadata Store | JSON sidecar | Stores source URL and scrape date per chunk |

**Data Sources (Groww only):**

| Source | Content Extracted | URL |
|---|---|---|
| Groww – HDFC Mid Cap | Expense ratio, exit load, SIP min, benchmark, riskometer, fund manager | https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth |
| Groww – HDFC Small Cap | Expense ratio, exit load, SIP min, benchmark, riskometer, fund manager | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth |
| Groww – HDFC Gold FoF | Expense ratio, exit load, SIP min, benchmark, riskometer, fund manager | https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth |
| Groww – HDFC Large Cap | Expense ratio, exit load, SIP min, benchmark, riskometer, fund manager | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth |
| Groww – HDFC ELSS | Expense ratio, exit load, SIP min, lock-in period, benchmark, riskometer | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth |

---

### 3.2 Query Classifier

A lightweight rule-based or LLM-based classifier that routes each incoming query.

```
Query
  │
  ├── Contains advisory intent keywords?
  │     (e.g., "should I", "better fund", "recommend", "invest in")
  │     └── YES → Refusal Handler
  │
  ├── Contains PII?
  │     (PAN, Aadhaar, account number, OTP, email, phone)
  │     └── YES → PII Guard → Reject with privacy notice
  │
  └── Factual query about scheme details?
        └── YES → Retrieval Pipeline
```

**Implementation:** Zero-shot classification using a small prompt or keyword regex list. No user data is stored.

---

### 3.3 Retrieval Engine

| Parameter | Value |
|---|---|
| Retrieval method | Dense vector similarity (cosine) |
| Top-K chunks | 3–5 most relevant chunks |
| Re-ranking | Optional cross-encoder re-ranker (e.g., `ms-marco-MiniLM`) |
| Fallback | If similarity score < threshold → "No information found" response |

---

### 3.4 Prompt Builder

Constructs the final prompt sent to the LLM. The system prompt enforces all response constraints defined in the problem statement.

```
SYSTEM PROMPT (injected at every call):
────────────────────────────────────────────────────────
You are a facts-only mutual fund FAQ assistant.

Rules:
1. Answer ONLY using the provided context. Do not infer or hallucinate.
2. Your response must be at most 3 sentences.
3. Include exactly one source URL citation at the end of your response.
4. Append the footer: "Last updated from sources: <date>"
5. NEVER provide investment advice, recommendations, or performance comparisons.
6. If the answer is not in the context, say: "I could not find this information
   in the official sources. Please visit [source URL] for details."
────────────────────────────────────────────────────────

CONTEXT (retrieved chunks):
{chunk_1}
{chunk_2}
{chunk_3}

USER QUERY:
{user_query}
```

---

### 3.5 Refusal Handler

Triggered for advisory or out-of-scope queries.

**Response template:**
```
I'm designed to answer only factual questions about mutual fund schemes
(e.g., expense ratios, exit loads, SIP minimums).

I'm not able to provide investment advice or fund recommendations.
For guidance, please visit: https://www.amfiindia.com/investor-corner
```

**Refusal trigger examples:**

| Query | Trigger | Action |
|---|---|---|
| "Should I invest in HDFC ELSS?" | Advisory intent | Refusal + AMFI link |
| "Which is the best HDFC fund?" | Comparison/recommendation | Refusal + AMFI link |
| "Will this fund give 20% returns?" | Performance prediction | Refusal + factsheet link |
| "My PAN is ABCDE1234F, check my portfolio" | PII detected | PII rejection notice |

---

### 3.6 Response Formatter

Applies post-processing to every LLM output before returning to the user.

| Step | Action |
|---|---|
| Sentence truncation | Trim to max 3 sentences if LLM exceeds limit |
| Citation injection | Append source URL if missing |
| Footer injection | Append `"Last updated from sources: <date>"` |
| Disclaimer | Append `"Facts-only. No investment advice."` |
| PII scan | Strip any PII that may have leaked into output |

---

### 3.7 Frontend (UI Layer)

A minimal, single-page web interface.

| UI Element | Description |
|---|---|
| Welcome Banner | Greeting + brief description of the assistant |
| Example Questions | 3 pre-filled clickable query suggestions |
| Chat Interface | Input box + response display area |
| Disclaimer Banner | Persistent: `"Facts-only. No investment advice."` |
| Source Footer | Rendered below each answer with date |

**Tech stack options:**

| Option | Stack |
|---|---|
| Lightweight | HTML + CSS + Vanilla JS (single file) |
| Framework-based | Next.js / Vite + React |
| Rapid prototype | Streamlit (Python) |

---

## 4. Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| Language | Python 3.10+ | Ecosystem for NLP/RAG (LangChain, HuggingFace) |
| RAG Framework | LangChain | Modular retrieval + prompt chaining |
| Embedding Model | `all-MiniLM-L6-v2` (local, HuggingFace) | Free, fast, accurate semantic search — no API cost |
| Vector Store | ChromaDB (local) | Zero-infrastructure, persistent, easy to reset |
| LLM | **Groq** – `llama-3.3-70b-versatile` | Ultra-fast inference (~500 tok/s), free tier, instruction-following |
| Web Scraper | `BeautifulSoup4` + `Requests` | Scrapes all 5 Groww scheme pages |
| Frontend | Streamlit or HTML/CSS/JS | Minimal UI, fast iteration |
| Metadata Store | JSON | Lightweight, no server needed |

---

## 5. Data Flow

```
Step 1: INGEST
  Scrape 5 Groww scheme URLs → Clean HTML text → Chunk (300–500 tokens)
  → Embed (all-MiniLM-L6-v2) → Store in ChromaDB with metadata {source_url, scrape_date}

Step 2: QUERY (Runtime)
  User types query
  → Classify (factual / advisory / PII)
  → [Advisory] → Refusal Handler → Return polite refusal
  → [Factual]  → Embed query → Retrieve top-K chunks
                → Build prompt (system + context + query)
                → Call LLM → Format response
                → Return: answer + source URL + date footer
```

---

## 6. Facts Covered Per Scheme

Each scheme page scrape is expected to capture:

| Data Point | Source |
|---|---|
| Fund category | Groww scheme page |
| Expense ratio (Direct plan) | Groww scheme page |
| Exit load | Groww scheme page |
| Minimum SIP amount | Groww scheme page |
| Minimum lump sum amount | Groww scheme page |
| Lock-in period (ELSS only) | Groww scheme page |
| Riskometer classification | Groww scheme page |
| Benchmark index | Groww scheme page |
| Fund manager name | Groww scheme page |
| AUM | Groww scheme page |

---

## 7. Security & Privacy Design

| Concern | Mitigation |
|---|---|
| PII in queries | Regex-based PII detector before any processing |
| Data storage | No user queries or inputs are stored or logged |
| Source integrity | Only whitelisted official domains are scraped |
| LLM hallucination | Strict system prompt; fallback when context is empty |
| Advisory leakage | Query classifier + system prompt double-guard |

---

## 8. Known Limitations

| Limitation | Detail |
|---|---|
| Static knowledge base | Scrape must be re-run to reflect NAV/expense ratio changes |
| No real-time NAV | Live NAV data is not fetched; displayed NAV on Groww used instead |
| Single AMC scope | Only HDFC schemes covered; other AMCs out of scope |
| Groww page dependency | If Groww changes page layout or goes down, scraper must be updated |
| LLM context window | Very long documents may be truncated during retrieval |
| Language support | English only; no vernacular language support |

---

## 9. Folder Structure

```
ragchatbot/
│
├── data/
│   ├── raw/                  # Scraped HTML from Groww pages
│   ├── processed/            # Cleaned, chunked text files
│   └── metadata.json         # Source URL + scrape date per document
│
├── ingestion/
│   ├── scraper.py            # Groww page scraper (BeautifulSoup + Requests)
│   ├── chunker.py            # Text splitting and overlap logic
│   └── embedder.py           # Embedding + ChromaDB ingestion
│
├── retrieval/
│   ├── retriever.py          # Vector similarity search (top-K)
│   └── reranker.py           # Optional cross-encoder re-ranking
│
├── pipeline/
│   ├── classifier.py         # Query intent classification
│   ├── prompt_builder.py     # System prompt + context assembly
│   ├── llm_client.py         # LLM API wrapper (Gemini / OpenAI)
│   ├── response_formatter.py # Post-processing: truncation, footer, citation
│   └── refusal_handler.py    # Refusal response templates
│
├── ui/
│   ├── app.py                # Streamlit app (or index.html for web)
│   └── static/               # CSS / JS assets (if HTML frontend)
│
├── vector_store/
│   └── chroma_db/            # Persisted ChromaDB vector index
│
├── config.py                 # API keys, model names, config constants
├── requirements.txt          # Python dependencies
├── problemstatement.md       # Project problem statement
├── architecture.md           # This document
└── README.md                 # Setup and usage instructions
```

---

## 10. Response Examples

### Factual Query (Success)
> **Q:** What is the expense ratio of HDFC Mid Cap Fund Direct Growth?

> **A:** The HDFC Mid Cap Opportunities Fund - Direct Plan has an expense ratio of **0.77% per annum** as of the latest factsheet. This applies to the Direct Growth variant and is lower than the Regular plan due to the absence of distributor commissions.
> **Source:** https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth
> *Last updated from sources: August 2025*

---

### Advisory Query (Refusal)
> **Q:** Should I invest in HDFC ELSS to save tax?

> **A:** I can only provide factual information about mutual fund schemes — I'm not able to offer investment advice or tax recommendations. For ELSS-related education, please visit the AMFI investor corner.
> **Source:** https://www.amfiindia.com/investor-corner
> *Last updated from sources: August 2025*

---

## 11. Scalability & Future Enhancements

| Enhancement | Description |
|---|---|
| Multi-AMC support | Extend corpus to SBI, Axis, Nippon fund pages |
| Scheduled re-ingestion | Cron job to refresh scrapes monthly |
| Hybrid search | Combine BM25 (keyword) + dense vector retrieval |
| Confidence scoring | Display retrieval confidence to user |
| Audit logging | Log query intent + source used (no PII) for quality review |
| Multilingual support | Hindi/regional language query handling |

---

> **Disclaimer:** Facts-only. No investment advice.

