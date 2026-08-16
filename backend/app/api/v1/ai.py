# ─────────────────────────────────────────────────────────
# ai.py — AI endpoints (summary, incident analysis, report)
# ─────────────────────────────────────────────────────────
# These endpoints are the "brain" of the app. Each one:
#   1. gathers data from GLPI / OpenProject endpoints
#   2. builds a prompt (services/prompts.py)
#   3. asks llama.cpp (services/llamacpp.py)
#   4. returns the AI-generated text
#
# The heavy lifting lives in backend/app/services/
#
# Note: we reuse the data-gathering functions defined in
# glpi.py and openproject.py instead of duplicating HTTP calls.
# ─────────────────────────────────────────────────────────

from fastapi import APIRouter

from backend.app.api.v1.glpi import list_tickets, ticket_stats
from backend.app.api.v1.openproject import work_package_stats
from backend.app.services.llamacpp import chat_completion
from backend.app.services.prompts import (
    build_incident_analysis_messages,
    build_report_messages,
    build_summary_messages,
)

# All routes in this file live under /api/v1/ai
router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/summary")
async def ai_summary():
    """Generate a human-language project status summary.
    # Gather GLPI ticket stats + OpenProject work-package stats, build the summary
    # prompt from them, send it to llama.cpp, and return the AI's plain-language text.
    Flow:
      1. Gather ticket stats from GLPI.
      2. Gather work-package stats from OpenProject.
      3. Ask llama.cpp for a plain-language summary.
    """
    t_stats = await ticket_stats()
    wp_stats = await work_package_stats()

    messages = build_summary_messages(t_stats, wp_stats)
    text = await chat_completion(messages)

    return {"section": "summary", "data": {"tickets": t_stats, "work_packages": wp_stats}, "ai_text": text}


@router.post("/incident-analysis")
async def ai_incident_analysis():
    """Analyze the current GLPI incidents."""
    # Fetch all GLPI tickets, build the incident-analysis prompt from them, send it
    # to llama.cpp, and return the AI's findings (common themes, recurrences, priorities).
    """Analyze the current GLPI incidents.

    Flow:
      1. Fetch all tickets from GLPI.
      2. Ask llama.cpp to analyze them (common themes, recurrences).
    """
    tickets = await list_tickets()

    messages = build_incident_analysis_messages(tickets)
    text = await chat_completion(messages)

    return {
        "section": "incident_analysis",
        "data": {"ticket_count": len(tickets)},
        "ai_text": text,
    }


@router.post("/report")
async def ai_report():
    """Generate the structured "Company Status" report."""
    # Gather GLPI + OpenProject stats, build the strict-format report prompt, send it
    # to llama.cpp, and return the AI's report (IT Support / Development / Risks).
    """Generate the structured "Company Status" report.

    Flow:
      1. Gather ticket stats from GLPI.
      2. Gather work-package stats from OpenProject.
      3. Ask llama.cpp to produce the exact MVP report format.
    """
    t_stats = await ticket_stats()
    wp_stats = await work_package_stats()

    messages = build_report_messages(t_stats, wp_stats)
    text = await chat_completion(messages)

    return {"section": "report", "data": {"tickets": t_stats, "work_packages": wp_stats}, "ai_text": text}
