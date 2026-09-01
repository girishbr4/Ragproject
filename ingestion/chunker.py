# ingestion/chunker.py
"""
Text cleaner and chunker for scraped mutual fund content.

Strategy (updated based on analysis of actual processed data):
  1. Strip noise blocks — Groww site nav, footer boilerplate, and the
     "--- Full Page Content ---" sentinel are removed before chunking.
  2. Section-aware split — the structured header (facts extracted by the
     scraper) is kept as a single atomic chunk so retrieval always has a
     dense, self-contained facts block.
  3. Larger chunks with higher overlap — real content is richer, so we
     use 800 chars (approx 200 tokens for bge-small-en-v1.5) with 120-char
     overlap to keep context across split boundaries.
  4. Min-length filter — chunks shorter than MIN_CHUNK_CHARS are dropped
     (they are navigation bullets or degenerate splitter artefacts).
  5. Deduplication — identical chunk texts are removed to avoid wasting
     embedding slots on repeated boilerplate.
  6. chunk_type tagging — each chunk is labelled with one of:
       structured_facts — header / key-facts block (always retrieved first)
       faq_text         — FAQ paragraphs with factual sentences
       fund_description — investment objective / scheme description
       holdings         — portfolio stock/sector/weight rows
       noise            — nav/footer leftovers (excluded from ChromaDB)
"""

import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP

# ── Tunables ──────────────────────────────────────────────────────────────────
# Override plan defaults: character-based splitter needs larger values than
# "400 tokens" to produce meaningful chunks (bge-small-en-v1.5 is char-based).
_CHUNK_SIZE    = max(CHUNK_SIZE, 800)    # at least 800 chars
_CHUNK_OVERLAP = max(CHUNK_OVERLAP, 120) # at least 120 chars
MIN_CHUNK_CHARS = 60                     # drop degenerate/tiny chunks

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=_CHUNK_SIZE,
    chunk_overlap=_CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " "],
)

# ── Noise patterns to strip from the full-page content section ───────────────
# These are blocks that appear in every Groww page but carry zero fund-specific
# signal: site-wide navigation, the footer alphabet lists, boilerplate calculators.
_NOISE_BLOCKS: list[re.Pattern] = [
    # Groww top-nav menu items repeated across all pages
    re.compile(
        r"(Stocks\nInvest in Stocks.*?Login/Sign up)",
        re.DOTALL,
    ),
    # Footer: fund name lists A-Z ("Mutual Funds:\nA\nB\nC...")
    re.compile(
        r"Mutual Funds:\s*\nA\nB\nC.*",
        re.DOTALL,
    ),
    # Footer: Stocks A-Z list
    re.compile(
        r"Stocks:\s*\nA\nB\nC.*",
        re.DOTALL,
    ),
    # Footer: contact/address block and everything after Groww address
    re.compile(
        r"Vaishnavi Tech Park.*",
        re.DOTALL,
    ),
    # Groww AMC/fund comparison noise lists
    re.compile(
        r"(Compare similar funds\nName\n1Y\n3Y\nFund Size.*?Compare\n)",
        re.DOTALL,
    ),
    # "Also manages these schemes" lists (long repeated fund names)
    re.compile(
        r"Also manages these schemes\n(HDFC [^\n]+\n){3,}",
        re.DOTALL,
    ),
    # The sentinel line itself — not useful as a standalone chunk
    re.compile(r"^--- Full Page Content ---\s*$", re.MULTILINE),
    # "Search Groww....\nCtrl+K\nLogin/Sign up" artefact
    re.compile(r"Search Groww\.\.\.\.\nCtrl\+K\nLogin/Sign up\n?"),
]

# ── Residual noise signals (post-regex cleanup) ──────────────────────────────
# Chunks that pass the regex cleaner but still carry zero factual signal.
_RESIDUAL_NOISE_TOKENS = [
    "Gold Petal Future",
    "Crude Oil Mini Future",
    "Silver Micro Future",
    "NSE\nBSE\nMCX",
    "Groww IFSC",
    "SIP Calculator",
    "Brokerage Calculator",
    "IPO Subscription Status",
    "Download the App",
    "Trust & Safety",
    "SMART ODR",
    "Bug Bounty",
]

# Lines that are pure site-navigation bullets — filter at line level
_NAV_LINE_PATTERNS: list[re.Pattern] = [
    re.compile(r"^(Intraday|ETF Screener|MTFs|Stock Screener|Stock Events|"
               r"Demat Account|Share Market Today|F&O|Trade in Futures|"
               r"Indices|Terminal|Option chain|Pledge|Commodities|"
               r"API trading|Mutual Fund Houses|NFO's|Mutual Funds by Groww|"
               r"Start SIP|Track Funds|Compare Funds|SIP calculator|"
               r"Brokerage calculator|Margin calculator|SWP calculator|"
               r"Pricing|Blog|Credit|Groww AMC|PMS|Bonds|"
               r"MF Screener|MF Knowledge Centre|NRI Demat Account|"
               r"HUF Demat Account|Groww Digest|Groww Charts|"
               r"Groww Terminal|915 Terminal|Stock Screens|Algo Trading)$"),
    # Footer index letters (single capital letters on their own line)
    re.compile(r"^[A-Z]$"),
    # Pure punctuation / operator lines
    re.compile(r"^[+\-\.%,>]+$"),
]


def classify_chunk_type(text: str, is_header: bool = False) -> str:
    """
    Assign a chunk_type label used by embedder.py and retriever.py.

    Labels (in priority order):
      structured_facts — the scraped key-facts block (always retrieved first)
      faq_text         — FAQ paragraphs with named factual fields
      fund_description — investment objective / scheme summary
      holdings         — stock / sector / weight rows
      noise            — residual nav/footer (skipped at embed time)
    """
    if is_header:
        return "structured_facts"

    # Residual noise check
    if any(token in text for token in _RESIDUAL_NOISE_TOKENS):
        return "noise"

    # FAQ text: contains factual named fields in prose
    faq_signals = (
        "Expense Ratio of", "AUM", "NAV of",
        "Exit load of", "Minimum SIP", "Minimum Lump",
        "average annual returns", "since its inception",
    )
    if any(sig in text for sig in faq_signals):
        return "faq_text"

    # Fund description: investment objective / mandate
    desc_signals = (
        "Investment Objective", "seeks to provide",
        "predominantly in", "long-term capital appreciation",
        "Fund benchmark",
    )
    if any(sig in text for sig in desc_signals):
        return "fund_description"

    # Holdings: repeated stock\nSector\nEquity\n% pattern
    if text.count("\nEquity\n") >= 3 or text.count("\nFinancial\n") >= 2:
        return "holdings"

    return "faq_text"  # safe default for remaining cleaned body text



def _strip_noise(text: str) -> str:
    """
    Remove Groww site navigation and footer boilerplate from page text.
    Only the "Full Page Content" section is cleaned; the structured header
    produced by _build_structured_text() in scraper.py is left untouched.
    """
    # Apply block-level regex removals
    for pattern in _NOISE_BLOCKS:
        text = pattern.sub("", text)

    # Line-level nav filter
    cleaned_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if any(p.match(stripped) for p in _NAV_LINE_PATTERNS):
            continue
        cleaned_lines.append(line)

    # Collapse excessive blank lines left by removals
    result = re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned_lines))
    return result.strip()


def _split_header_from_body(text: str) -> tuple[str, str]:
    """
    Split the document into:
      - header: everything up to (and including) the structured facts block
      - body:   everything after "--- Full Page Content ---"

    The header is kept as a single atomic chunk; the body is split normally.
    If the sentinel is absent the whole text is treated as body.
    """
    sentinel = "--- Full Page Content ---"
    idx = text.find(sentinel)
    if idx == -1:
        return "", text

    # Header ends just before the sentinel; body starts after it
    header = text[:idx].strip()
    body   = text[idx + len(sentinel):].strip()
    return header, body


def chunk_document(
    text: str,
    source_url: str,
    scrape_date: str,
    scheme_name: str = "",
) -> list[dict]:
    """
    Split *text* into clean, meaningful chunks and attach metadata to each.

    Pipeline:
      1. Split into header (structured facts) + body (full page text).
      2. Strip navigation/footer noise from the body.
      3. Keep the header as one atomic chunk tagged "structured_facts".
      4. Split body with RecursiveCharacterTextSplitter.
      5. Drop chunks shorter than MIN_CHUNK_CHARS.
      6. Deduplicate identical chunk texts.
      7. Classify each body chunk with classify_chunk_type().

    Args:
        text:        Cleaned plain text to split (output of scraper).
        source_url:  Origin URL for citation.
        scrape_date: ISO date string (YYYY-MM-DD) of when content was fetched.
        scheme_name: Human-readable scheme name for filtering (optional).

    Returns:
        List of chunk dicts:
          {text, source_url, date, scheme_name, chunk_type}
        chunk_type == "noise" chunks are included for audit (saved to
        data/processed/) but are filtered out by embedder.py.
    """
    def _make_chunk(t: str, chunk_type: str) -> dict:
        return {
            "text":        t,
            "source_url":  source_url,
            "date":        scrape_date,
            "scheme_name": scheme_name,
            "chunk_type":  chunk_type,
        }

    header, body = _split_header_from_body(text)
    body_clean   = _strip_noise(body)

    results: list[dict] = []
    seen:    set[str]   = set()

    # ── 1. Header chunk (atomic — always structured_facts) ──────────────────
    if header and len(header) >= MIN_CHUNK_CHARS:
        results.append(_make_chunk(header, "structured_facts"))
        seen.add(header)

    # ── 2. Body chunks ─────────────────────────────────────────────────────
    for chunk_text in _splitter.split_text(body_clean):
        chunk_text = chunk_text.strip()
        if len(chunk_text) < MIN_CHUNK_CHARS:
            continue          # drop tiny/degenerate chunks
        if chunk_text in seen:
            continue          # deduplicate
        seen.add(chunk_text)
        chunk_type = classify_chunk_type(chunk_text)
        results.append(_make_chunk(chunk_text, chunk_type))

    return results
