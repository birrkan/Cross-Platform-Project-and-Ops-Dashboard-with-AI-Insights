# ─────────────────────────────────────────────────────────
# router.py — Collects all route files into one place
# ─────────────────────────────────────────────────────────
# main.py imports this single file instead of importing
# every route file individually.
#
# Reference: https://fastapi.tiangolo.com/tutorial/bigger-applications/#apirouter
# ─────────────────────────────────────────────────────────

from fastapi import APIRouter

from backend.app.api.v1.llamacpp import router as llamacpp_router


api_v1_router = APIRouter()

# Each include_router adds a group of endpoints under /api/v1
api_v1_router.include_router(llamacpp_router)
