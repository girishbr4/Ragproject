"""
Debug: print the cleaned page text around key field labels to tune regex patterns.
Run with:  python scripts/debug_text.py
"""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bs4 import BeautifulSoup
from ingestion.scraper import _clean_text

html = Path("data/raw/hdfc-elss-tax-saver-fund-direct-plan-growth.html").read_text(encoding="utf-8")
soup = BeautifulSoup(html, "lxml")
for tag in soup.find_all(["script", "style", "nav", "footer", "noscript", "svg", "iframe"]):
    tag.decompose()

raw_text = soup.get_text(separator="\n", strip=True)
text = _clean_text(raw_text)

# Print lines around keywords
KEYWORDS = ["expense ratio", "exit load", "sip", "lump", "risk", "benchmark",
            "fund manager", "lock", "category", "elss", "3 year", "minimum"]

lines = text.splitlines()
for i, line in enumerate(lines):
    if any(kw in line.lower() for kw in KEYWORDS):
        start = max(0, i-1)
        end   = min(len(lines), i+3)
        print(f"[L{i:04d}] " + "\n        ".join(lines[start:end]))
        print()
