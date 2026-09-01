# 💼 HDFC Mutual Fund FAQ Assistant

> **Disclaimer:** Facts-only. No investment advice.

A Retrieval-Augmented Generation (RAG) chatbot that answers **factual questions** about 5 HDFC Mutual Fund schemes using official Groww scheme pages as its sole knowledge source.

---

## Selected AMC & Schemes

**AMC:** HDFC Mutual Fund

| Scheme | Source URL |
|---|---|
| HDFC Mid Cap Fund – Direct Growth | https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth |
| HDFC Small Cap Fund – Direct Growth | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth |
| HDFC Gold ETF Fund of Fund – Direct Growth | https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth |
| HDFC Large Cap Fund – Direct Growth | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth |
| HDFC ELSS Tax Saver Fund – Direct Growth | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth |

---

## Architecture

See [`architecture.md`](architecture.md) for the full system design.

---

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd ragchatbot
```

### 2. Create & activate virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

```bash
copy .env.example .env          # Windows
# or
cp .env.example .env            # macOS / Linux
```

Edit `.env` and set your Groq API key:
```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free key at https://console.groq.com.

### 5. Run the ingestion pipeline

```bash
python ingest_all.py
```

This scrapes the 5 Groww scheme pages, chunks the text, embeds it with `all-MiniLM-L6-v2`, and stores everything in ChromaDB.

### 6. Launch the UI

```bash
streamlit run ui/app.py
```

Open http://localhost:8501 in your browser.

---

## Re-running Ingestion

To refresh the knowledge base (e.g. after scheme data changes):

```bash
python ingest_all.py
```

The pipeline uses `upsert` so re-runs are idempotent — no duplicates.

---

## Project Structure

```
ragchatbot/
├── data/
│   ├── raw/                 # Scraped HTML (gitignored)
│   ├── processed/           # Chunked JSON (gitignored)
│   └── metadata.json        # Scrape timestamps & chunk counts
├── ingestion/
│   ├── scraper.py           # Groww page scraper
│   ├── pdf_parser.py        # PDF parser stub
│   ├── chunker.py           # Text chunker
│   └── embedder.py          # ChromaDB ingestion
├── retrieval/
│   ├── retriever.py         # Similarity search
│   └── reranker.py          # Cross-encoder reranker stub
├── pipeline/
│   ├── classifier.py        # Intent classifier (advisory / PII / factual)
│   ├── prompt_builder.py    # Prompt construction
│   ├── llm_client.py        # Groq API client
│   ├── response_formatter.py# Output post-processing
│   ├── refusal_handler.py   # Canned refusals
│   └── main.py              # Pipeline orchestrator
├── ui/
│   ├── app.py               # Streamlit UI
│   └── static/              # Static assets
├── vector_store/
│   └── chroma_db/           # ChromaDB persistence (gitignored)
├── config.py                # All configuration constants
├── ingest_all.py            # Ingestion pipeline runner
├── requirements.txt
└── README.md
```

---

## Known Limitations

See `architecture.md §8` for the full list. Key limitations:

- **No live NAV data** — NAV is not scraped (changes daily); queries about today's NAV return a factsheet link only.
- **No PDF ingestion** — Only Groww scheme page content is indexed.
- **Groww layout changes** — If Groww restructures their pages, the scraper CSS selectors will need updating.
- **5 schemes only** — Limited to the 5 HDFC schemes listed above.
- **Groq dependency** — Requires an active Groq API key; no offline LLM fallback.

---

> **Disclaimer:** Facts-only. No investment advice. For investment decisions, consult a SEBI-registered financial advisor.
