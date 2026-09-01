"""
Quick smoke test: scrape just the HDFC ELSS page and print the extracted fields.
Run with:  python scripts/test_scrape_one.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.scraper import scrape_scheme

URL = "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth"

print(f"Scraping: {URL}\n")
result = scrape_scheme(URL)

print("\n-- Extracted Fields ----------------------------------------")
for k, v in result["fields"].items():
    status = "[Y]" if v else "[N]"
    print(f"  {status} {k:20s}: {v or '(not found)'}")

print(f"\n-- Content Preview (first 800 chars) -----------------------")
print(result["content"][:800])
print(f"\nTotal content length: {len(result['content']):,} chars")
print(f"Raw HTML saved to:    data/raw/{result['slug']}.html")
