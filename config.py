# config.py
import os
from dotenv import load_dotenv

# Force UTF-8 stdout/stderr on Windows to prevent cp1252 UnicodeEncodeErrors
os.environ.setdefault("PYTHONUTF8", "1")

load_dotenv()

# ── LLM Settings ─────────────────────────────────────────────────────────────
LLM_PROVIDER       = "groq"                      # Groq API
LLM_MODEL          = "openai/gpt-oss-120b"        # Groq-hosted OpenAI-compatible model

# ── Embedding & Vector Store ──────────────────────────────────────────────────
EMBEDDING_MODEL    = "BAAI/bge-small-en-v1.5"    # BGE small — outperforms MiniLM on retrieval benchmarks
CHROMA_DB_PATH     = "vector_store/chroma_db"

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE         = 400    # tokens
CHUNK_OVERLAP      = 60

# ── Retrieval ─────────────────────────────────────────────────────────────────
TOP_K              = 4      # number of chunks to retrieve
SIMILARITY_THRESHOLD = 0.35

# ── Response ─────────────────────────────────────────────────────────────
MAX_RESPONSE_SENTENCES = 3
LLM_MAX_TOKENS         = 200   # keep low: 3 sentences needs ~100 tokens

# ── Rate Limit Config (openai/gpt-oss-120b free tier on Groq) ────────────────
# Limits: 30 RPM | 1K req/day | 8K tokens/min | 200K tokens/day
LLM_MAX_RETRIES        = 3     # retry attempts on 429 RateLimitError
LLM_RETRY_BASE_DELAY   = 2.0   # seconds — doubles each retry (2, 4, 8 s)
LLM_CACHE_SIZE         = 256   # LRU cache: max unique queries cached in memory

# ── Domain Whitelist ──────────────────────────────────────────────────────────
WHITELISTED_DOMAINS = [
    "groww.in",
    "amfiindia.com",
    "sebi.gov.in",
    "hdfcfund.com",
    "camsonline.com",
    "kfintech.com",
]

# ── Scheme URLs (5 HDFC schemes on Groww) ─────────────────────────────────────
SCHEME_URLS = [
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
]

# ── Scheduler / Freshness ─────────────────────────────────────────────────────
# How many days old can scrape_date be before the UI shows a stale-data warning?
# Overridable via .env or GitHub Actions / Railway environment variables.
STALE_DATA_THRESHOLD_DAYS = int(os.getenv("STALE_DATA_THRESHOLD_DAYS", "2"))
