# ─────────────────────────────────────────────────────────
# main.py — FastAPI app entry point
# ─────────────────────────────────────────────────────────
# Run with: uvicorn backend.app.main:app --reload
#
# Reference: https://fastapi.tiangolo.com/tutorial/first-steps/#create-it
# ─────────────────────────────────────────────────────────

from fastapi import FastAPI

from backend.app.api.v1.router import api_v1_router
from backend.app.config import settings


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

app.include_router(api_v1_router, prefix="/api/v1")
