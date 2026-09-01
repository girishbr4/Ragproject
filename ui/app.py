# ui/app.py
"""
Streamlit chat UI for the HDFC Mutual Fund FAQ Assistant.

Run with:
    streamlit run ui/app.py
"""
import sys
from pathlib import Path

# Ensure project root is on sys.path when launched from the ui/ subdirectory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from pipeline.main import answer

st.set_page_config(
    page_title="HDFC Fund FAQ",
    page_icon="💼",
    layout="centered",
)

# ── Disclaimer banner ──────────────────────────────────────────────────────────
st.warning("⚠️ Facts-only. No investment advice.")

st.title("💼 HDFC Mutual Fund FAQ Assistant")
st.caption(
    "Answers factual questions about HDFC mutual fund schemes using official "
    "sources only. Not financial advice."
)

# ── Example questions ──────────────────────────────────────────────────────────
st.markdown("**Try asking:**")
EXAMPLES = [
    "What is the expense ratio of HDFC Mid Cap Fund Direct Growth?",
    "What is the exit load for HDFC ELSS Tax Saver Fund?",
    "What is the minimum SIP amount for HDFC Small Cap Fund?",
]
for ex in EXAMPLES:
    if st.button(ex, key=f"example_{ex[:20]}"):
        st.session_state["prefill_query"] = ex

# ── Chat history ───────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Chat input ─────────────────────────────────────────────────────────────────
prefill = st.session_state.pop("prefill_query", None)
query   = st.chat_input(
    placeholder="Ask a factual question about an HDFC mutual fund scheme...",
)
query = query or prefill

if query:
    st.session_state["messages"].append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving from official sources..."):
            response = answer(query)
        st.markdown(response)

    st.session_state["messages"].append({"role": "assistant", "content": response})
