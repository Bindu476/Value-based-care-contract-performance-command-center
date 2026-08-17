"""
backend/app/main.py — FastAPI entrypoint. Serves the precomputed analytical artifacts
built in Phases 2-11. No live recomputation on request — reads parquet/csv, per Section 24.
"""
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import dashboard, acos, providers, hospitals, opportunities, review, contracts

app = FastAPI(title="VBC Payer Command Center API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local dev only, per Section 38 (no auth/multi-tenant in v1)
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api")
app.include_router(acos.router, prefix="/api")
app.include_router(providers.router, prefix="/api")
app.include_router(hospitals.router, prefix="/api")
app.include_router(opportunities.router, prefix="/api")
app.include_router(review.router, prefix="/api")
app.include_router(contracts.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
