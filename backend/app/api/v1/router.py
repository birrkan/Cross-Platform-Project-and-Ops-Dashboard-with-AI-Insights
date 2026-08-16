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
from backend.app.api.v1.glpi import router as glpi_router
from backend.app.api.v1.openproject import router as openproject_router
from backend.app.api.v1.xwiki import router as xwiki_router


api_v1_router = APIRouter()

# Each include_router adds a group of endpoints under /api/v1
api_v1_router.include_router(llamacpp_router)
api_v1_router.include_router(glpi_router)
api_v1_router.include_router(openproject_router)
api_v1_router.include_router(xwiki_router)
