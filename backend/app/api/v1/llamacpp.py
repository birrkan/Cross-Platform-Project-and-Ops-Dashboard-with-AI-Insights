# ─────────────────────────────────────────────────────────
# llamacpp.py — Routes for llama.cpp status and interaction
# ─────────────────────────────────────────────────────────
#
# Reference: https://fastapi.tiangolo.com/tutorial/path-params/
# ─────────────────────────────────────────────────────────

import httpx
from fastapi import APIRouter

from backend.app.config import settings


router = APIRouter(prefix="/llamacpp", tags=["llamacpp"])


@router.get("/status")
async def llamacpp_status():
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{settings.llamacpp_base_url}/models")

    data = response.json()
    model_name = data["models"][0]["name"]

    return {
        "status": "ok",
        "model": model_name,
    }
