from asyncio import gather

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
