from asyncio import gather
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from httpx import AsyncClient

from backend.app.config import settings

router = APIRouter(prefix="/glpi", tags=["glpi"])


async def _get_token() -> str:
    async with AsyncClient() as client:
        resp = await client.post(
            f"{settings.glpi_api_url}/api.php/token",
            data={
                "grant_type": "password",
                "client_id": settings.glpi_client_id,
                "client_secret": settings.glpi_client_secret,
                "username": settings.glpi_username,
                "password": settings.glpi_password,
                "scope": "api",
            },
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"GLPI auth failed: {resp.text}",
        )
    return resp.json()["access_token"]


@router.get("/tickets")
async def list_tickets():
    token = await _get_token()
    async with AsyncClient() as client:
        resp = await client.get(
            f"{settings.glpi_api_url}{settings.glpi_api_path}/Assistance/Ticket/",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


ACTIVE_STATUS_IDS = {1, 2, 3, 4}


@router.get("/tickets/stats")
async def ticket_stats():
    tickets = await list_tickets()

    total = len(tickets)
    active = 0
    solved = 0
    by_status = defaultdict(int)
    by_urgency = defaultdict(int)
    by_day = defaultdict(int)

    today = datetime.now().date()
    for t in tickets:
        if t.get("is_deleted"):
            continue

        status_id = t.get("status", {}).get("id")
        by_status[t.get("status", {}).get("name", "Unknown")] += 1
        by_urgency[f"urgency_{t.get('urgency', 0)}"] += 1

        if status_id in ACTIVE_STATUS_IDS:
            active += 1
        elif status_id in {5, 6}:
            solved += 1

        created = t.get("date", "")[:10]
        if created:
            try:
                by_day[datetime.fromisoformat(created).date()] += 1
            except ValueError:
                pass

    trend = []
    for offset in range(13, -1, -1):
        day = today - timedelta(days=offset)
        trend.append({"date": day.isoformat(), "count": by_day.get(day, 0)})

    return {
        "total": total,
        "active": active,
        "solved": solved,
        "by_status": dict(by_status),
        "by_urgency": dict(by_urgency),
        "trend_14d": trend,
    }


SUB_RESOURCES = {
    "followups": "Timeline/Followup",
    "tasks": "Timeline/Task",
    "documents": "Timeline/Document",
    "solutions": "Timeline/Solution",
    "validations": "Timeline/Validation",
    "costs": "Cost",
}


@router.get("/tickets/{ticket_id}/full")
async def get_ticket_full(ticket_id: int):
    token = await _get_token()
    base = f"{settings.glpi_api_url}{settings.glpi_api_path}/Assistance/Ticket/{ticket_id}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    async with AsyncClient() as client:
        urls = {key: f"{base}/{path}" for key, path in SUB_RESOURCES.items()}
        responses = await gather(
            client.get(f"{base}", headers=headers),
            *(client.get(url, headers=headers) for url in urls.values()),
        )

    ticket = responses[0]
    if ticket.status_code != 200:
        raise HTTPException(status_code=ticket.status_code, detail=ticket.text)

    result = ticket.json()
    for idx, key in enumerate(SUB_RESOURCES):
        sub = responses[idx + 1]
        result[key] = sub.json() if sub.status_code == 200 else []

    return result
