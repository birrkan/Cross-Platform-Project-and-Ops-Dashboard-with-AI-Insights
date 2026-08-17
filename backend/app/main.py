# ─────────────────────────────────────────────────────────
# main.py — FastAPI app entry point
# ─────────────────────────────────────────────────────────
# Run with: uvicorn backend.app.main:app --reload
#
# Reference: https://fastapi.tiangolo.com/tutorial/first-steps/#create-it
# ─────────────────────────────────────────────────────────

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.v1.router import api_v1_router
from backend.app.config import settings


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

app.include_router(api_v1_router, prefix="/api/v1")

# Serve the dashboard at the root URL
STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.get("/", include_in_schema=False)
async def dashboard():
    return FileResponse(STATIC_DIR / "dashboard.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
