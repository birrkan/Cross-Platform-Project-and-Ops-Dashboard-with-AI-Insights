# ─────────────────────────────────────────────────────────
# xwiki.py — FastAPI endpoints for XWiki (knowledge base)
# ─────────────────────────────────────────────────────────
# Read and write knowledge-base pages on OUR backend.
# The dashboard/AI layer uses these instead of calling XWiki
# directly.
#
# Scope: operations are LIMITED to the 3 knowledge-base spaces
# (folders) we own. Nothing else in XWiki is touched.
#
#   - "IncidentProblem Knowledge Base"  -> known incidents & fixes
#   - "Service Reports"                 -> periodic service/uptime reports
#   - "User-documentation"              -> how-to guides for end users
#
# IMPORTANT — XWiki references (dots, not slashes):
#   A page created in the XWiki UI under "User-documentation"
#   actually lives in a NESTED SPACE. E.g. creating the page
#   "user-doc-example-1" creates:
#
#     space:  User-documentation
#     nested: user-doc-example-1
#     page:   WebHome
#
#   The full reference (what XWiki calls "fullName") is dotted:
#     User-documentation.user-doc-example-1.WebHome
#
#   So to GET that page you must pass:
#     /api/v1/xwiki/pages/User-documentation.user-doc-example-1.WebHome
#
# XWiki REST API v1 docs (official):
#   REST API reference:
#     https://www.xwiki.org/xwiki/bin/view/Documentation/UserGuide/Features/XWikiRESTfulAPI
#   Authentication (Basic auth):
#     same page, "Authentication" section
#   Page resources (GET/PUT/DELETE):
#     same page, "Page resources" section
#
# Notes learned during development:
#   1. The username must be the FULL user reference, e.g.
#      `XWiki.birkan` — not just `birkan`.
#   2. Page creation/update uses PUT with a JSON body of
#      {title, syntax, content}.
#   3. Nested spaces make page references dotted:
#      Space.SubSpace.Page
# ─────────────────────────────────────────────────────────

from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from httpx import AsyncClient

from backend.app.config import settings

# All routes in this file live under /api/v1/xwiki
router = APIRouter(prefix="/xwiki", tags=["xwiki"])

# "xwiki" is the default wiki inside a single XWiki server.
XWIKI_REST_BASE = f"{settings.xwiki_url}/rest/wikis/xwiki"

# The only top-level spaces this API is allowed to touch.
KNOWLEDGE_SPACES = [
    "IncidentProblem Knowledge Base",
    "Service Reports",
    "User-documentation",
]


def _auth() -> tuple[str, str] | None:
    """HTTP Basic auth tuple for XWiki, or None if not configured.

    Reference: https://www.xwiki.org/xwiki/bin/view/Documentation/UserGuide/Features/XWikiRESTfulAPI (Authentication)
    """
    if settings.xwiki_username and settings.xwiki_password:
        return (settings.xwiki_username, settings.xwiki_password)
    return None


def _require_kb_space(space: str) -> None:
    """Reject any top-level space that is not one of our KB spaces."""
    if space not in KNOWLEDGE_SPACES:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Space '{space}' is not a knowledge-base space. "
                f"Allowed: {KNOWLEDGE_SPACES}"
            ),
        )


def _reference_to_rest_path(page_ref: str) -> str:
    """Convert a dotted XWiki reference to a REST URL path.

    XWiki references use dots as separators:
      "Service Reports.WebHome"                  -> 2 parts (space, page)
      "User-documentation.user-doc-example-1.WebHome" -> 3 parts

    The REST API nests them:
      /spaces/Service Reports/pages/WebHome
      /spaces/User-documentation/spaces/user-doc-example-1/pages/WebHome

    So: all parts except the last become spaces, the last is the page.
    """
    parts = page_ref.split(".")
    if len(parts) < 2:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid page reference. Use the dotted format, e.g. "
                "'Service Reports.WebHome' or "
                "'User-documentation.user-doc-example-1.WebHome'."
            ),
        )
    space_parts = parts[:-1]
    page = parts[-1]

    # Enforce that the TOP-LEVEL space is one of ours.
    _require_kb_space(space_parts[0])

    path = ""
    for sp in space_parts:
        path += f"/spaces/{quote(sp)}"
    path += f"/pages/{quote(page)}"
    return path


@router.get("/spaces")
async def list_spaces():
    async with AsyncClient() as client:
        resp = await client.get(
            f"{XWIKI_REST_BASE}/spaces",
            auth=_auth(),
            headers={"Accept": "application/json"},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return [
        {"name": s.get("name"), "url": s.get("xwikiRelativeUrl")}
        for s in resp.json().get("spaces", [])
        if s.get("name") in KNOWLEDGE_SPACES
    ]


@router.get("/spaces/{space}/pages")
async def list_pages(space: str):
    _require_kb_space(space)

    async with AsyncClient() as client:
        headers = {"Accept": "application/json"}
        pages_resp = await client.get(
            f"{XWIKI_REST_BASE}/spaces/{quote(space)}/pages",
            auth=_auth(),
            headers=headers,
        )
        children_resp = await client.get(
            f"{XWIKI_REST_BASE}/spaces/{quote(space)}/pages/WebHome/children?hierarchy=nestedpages",
            auth=_auth(),
            headers=headers,
        )

    if pages_resp.status_code != 200:
        raise HTTPException(status_code=pages_resp.status_code, detail=pages_resp.text)

    entries = []
    for p in pages_resp.json().get("pageSummaries", []):
        entries.append(
            {
                "type": "page",
                "name": p.get("name"),
                "title": p.get("title"),
                "fullName": p.get("fullName"),
                "author": p.get("author"),
                "version": p.get("version"),
                "url": p.get("xwikiRelativeUrl"),
            }
        )

    # Children that differ from the WebHome itself are nested spaces
    # (e.g. user-doc-example-1.WebHome lives in a nested space).
    if children_resp.status_code == 200:
        for p in children_resp.json().get("pageSummaries", []):
            if p.get("name") == "WebHome" and p.get("space") == space:
                continue
            entries.append(
                {
                    "type": "nested_space",
                    "name": p.get("space"),
                    "title": p.get("title"),
                    "fullName": p.get("fullName"),
                    "author": p.get("author"),
                    "version": p.get("version"),
                    "url": p.get("xwikiRelativeUrl"),
                }
            )

    return entries


@router.get("/pages/{page_ref:path}")
async def get_page(page_ref: str):
    """Return the full content of a page by dotted reference.

    The reference is dotted (XWiki fullName format):
      /api/v1/xwiki/pages/Service Reports.WebHome
      /api/v1/xwiki/pages/User-documentation.user-doc-example-1.WebHome

    The `content` field is the wiki text the AI reads as
    knowledge (e.g. how a past incident was resolved).
    """
    path = _reference_to_rest_path(page_ref)

    async with AsyncClient() as client:
        resp = await client.get(
            f"{XWIKI_REST_BASE}{path}",
            auth=_auth(),
            headers={"Accept": "application/json"},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


@router.put("/pages/{page_ref:path}")
async def put_page(page_ref: str, body: dict):
    """Create or update a page by dotted reference.

    Endpoint used: PUT /rest/wikis/xwiki/spaces/.../pages/{page}
    Docs: https://www.xwiki.org/xwiki/bin/view/Documentation/UserGuide/Features/XWikiRESTfulAPI (Page resources)

    Body (JSON):
      {
        "title":   "Page title",          # optional
        "content": "Wiki/plain text",      # the page body
        "syntax":  "plain/1.0"             # optional, default varies
      }

    - PUT with a non-existent page -> creates it (HTTP 201)
    - PUT with an existing page    -> updates it (HTTP 202/304)

    This is the "push" operation: the AI will use it to store
    incident write-ups and service reports into the wiki.
    """
    path = _reference_to_rest_path(page_ref)

    # Build the JSON body XWiki expects. Only pass the fields
    # the caller provided, so we don't wipe existing content
    # when someone just wants to change the title.
    payload = {}
    for key in ("title", "content", "syntax"):
        if key in body:
            payload[key] = body[key]

    async with AsyncClient() as client:
        resp = await client.put(
            f"{XWIKI_REST_BASE}{path}",
            auth=_auth(),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json=payload,
        )
    if resp.status_code not in {200, 201, 202, 204}:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return {
        "reference": page_ref,
        "status": resp.status_code,
        "url": f"{XWIKI_REST_BASE}{path}",
    }
