# ─────────────────────────────────────────────────────────
# openproject.py — FastAPI endpoints for OpenProject
# ─────────────────────────────────────────────────────────
# Talks to OpenProject's REST API (v3) and exposes a few
# endpoints on OUR backend. The dashboard/AI layer will use
# these instead of calling OpenProject directly.
#
# OpenProject API v3 docs (official):
#   Work packages endpoints:
#   https://www.openproject.org/docs/api/endpoints/work-packages/
# ─────────────────────────────────────────────────────────

from collections import Counter

from fastapi import APIRouter, HTTPException
from httpx import AsyncClient

from backend.app.config import settings

# All routes in this file live under /api/v1/openproject
router = APIRouter(prefix="/openproject", tags=["openproject"])


def _auth() -> tuple[str, str]:
    return ("apikey", settings.openproject_api_token)


@router.get("/work_packages")
async def list_work_packages():
    async with AsyncClient() as client:
        resp = await client.get(
            f"{settings.openproject_url}/api/v3/work_packages?pageSize=100",
            auth=_auth(),
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()["_embedded"]["elements"]


@router.get("/work_packages/stats")
async def work_package_stats():
    work_packages = await list_work_packages()

    # Counter is a dict that starts counting from 0 automatically.
    by_status = Counter()
    by_type = Counter()
    by_project = Counter()
    active = 0

    for wp in work_packages:
        # `_links.status.title` holds the human-readable status name.
        # .get(key, default) protects us if a link is missing.
        status = wp["_links"].get("status", {}).get("title", "Unknown")
        by_status[status] += 1
        by_type[wp["_links"].get("type", {}).get("title", "Unknown")] += 1
        by_project[wp["_links"].get("project", {}).get("title", "Unknown")] += 1

        # Any status that is NOT closed/done/cancelled counts as "active".
        if status.lower() not in {"closed", "done", "cancelled"}:
            active += 1

    # Return plain dicts (Counter is a subclass of dict but returning
    # a plain dict keeps the JSON response clean).
    return {
        "total": len(work_packages),
        "active": active,
        "by_status": dict(by_status),
        "by_type": dict(by_type),
        "by_project": dict(by_project),
    }


@router.get("/work_packages/{wp_id}")
async def get_work_package(wp_id: int):
    async with AsyncClient() as client:
        resp = await client.get(
            f"{settings.openproject_url}/api/v3/work_packages/{wp_id}",
            auth=_auth(),
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()
