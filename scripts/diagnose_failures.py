import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from retrieval.retriever import retrieve
from pipeline.main import answer

# ── 1. ELSS Exit Load ─────────────────────────────────────────────────────────
print("=== ELSS Exit Load — Retrieved Chunks ===")
chunks = retrieve("What is the exit load for HDFC ELSS Tax Saver Fund?")
for i, c in enumerate(chunks):
    print(f"\n[{i}] type={c['chunk_type']}")
    print(c["text"][:300])

# ── 2. Large Cap Benchmark ───────────────────────────────────────────────────
print("\n\n=== Large Cap Benchmark — Retrieved Chunks ===")
chunks2 = retrieve("What is the benchmark index of HDFC Large Cap Fund?")
for i, c in enumerate(chunks2):
    print(f"\n[{i}] type={c['chunk_type']}")
    print(c["text"][:300])

# ── 3. Check LLM benchmark response for hidden chars ─────────────────────────
print("\n\n=== Benchmark Full Answer (char-level) ===")
resp = answer("What is the benchmark index of HDFC Large Cap Fund?")
print(repr(resp[:200]))
print(f"Contains 'NIFTY 100': {'NIFTY 100' in resp}")
print(f"Contains 'nifty 100': {'nifty 100' in resp.lower()}")
# check for non-breaking space
nb = resp.replace('\u00a0', ' ')
print(f"After nbsp fix, contains 'nifty 100': {'nifty 100' in nb.lower()}")
