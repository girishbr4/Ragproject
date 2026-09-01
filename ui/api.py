"""
FastAPI backend — exposes the Python RAG pipeline as a JSON REST API.

Run with:
    uvicorn ui.api:app --reload --port 8000
"""
import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure project root is on sys.path when launched from ui/ subdirectory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.main import answer  # noqa: E402

app = FastAPI(
    title="HDFC Mutual Fund FAQ API",
    description="Facts-only RAG pipeline for HDFC mutual fund scheme queries.",
    version="1.0.0",
)

# Build allowed origins list — add Vercel URL from env if set
_ALLOWED_ORIGINS = [
    "http://localhost:3000",   # Next.js dev server
    "http://localhost:8000",   # FastAPI itself (for health check)
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
async def chat(req: QueryRequest) -> QueryResponse:
    result = answer(req.query)
    return QueryResponse(response=result)
