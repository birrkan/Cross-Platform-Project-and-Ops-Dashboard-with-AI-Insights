# ─────────────────────────────────────────────────────────
# ai.py — AI endpoints (summary, incident analysis, report)
# ─────────────────────────────────────────────────────────
# These endpoints are the "brain" of the app. Each one:
#   1. gathers data from GLPI / OpenProject endpoints
#   2. builds a prompt (services/prompts.py)
#   3. asks llama.cpp (services/llamacpp.py)
#   4. returns the AI-generated text
# ─────────────────────────────────────────────────────────

import time
from asyncio import gather
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from backend.app.api.v1.glpi import get_ticket_followups, list_tickets
from backend.app.api.v1.openproject import list_work_packages
from backend.app.services.llamacpp import chat_completion
from backend.app.services.prompts import (
    build_dev_report_messages,
    build_dev_summary_messages,
    build_incident_analysis_messages,
    build_incident_report_messages,
    build_incident_table,
    build_ops_summary_messages,
    build_work_package_table,
    compute_status_updates,
    split_work_packages,
)

# All routes in this file live under /api/v1/ai
router = APIRouter(prefix="/ai", tags=["ai"])

# "Last sprint" window for the report.
SPRINT_DAYS = 14

# GLPI statuses that count as "resolved/closed".
RESOLVED_STATUSES = {"Solved", "Closed"}


@router.post("/summary")
async def ai_summary():
    """Generate a project status summary split into OPS + DEV sides.

    - OPS Side: GLPI tickets (as a table with GLPI status + a
      "Status Update" column decided from the ticket status and
      its comments) + AI summary.
    - DEV Side: two tables — Tasks (features/stories) and
      Incidents (work packages that reference "[INC #N]").
      Each followed by an AI summary.
    """
    start = time.perf_counter()
    tickets = await list_tickets()
    work_packages = await list_work_packages()

    # Split dev work into incidents (reference [INC #N]) and tasks.
    dev_incidents, dev_tasks = split_work_packages(work_packages)

    # Fetch each ticket's comments so the Status Update column can
    # reflect reality (e.g. "resolved", "handed to dev", "waiting").
    followups = await gather(
        *(get_ticket_followups(t.get("id")) for t in tickets)
    )
    followups_by_ticket = {
        t.get("id"): f for t, f in zip(tickets, followups)
    }

    # OPS table: GLPI status + a Status Update column that reads the
    # ticket's status AND comments to decide the note.
    status_updates = compute_status_updates(tickets, followups_by_ticket, dev_incidents)

    ops_summary = await chat_completion(
        build_ops_summary_messages(tickets, status_updates)
    )
    dev_summary = await chat_completion(build_dev_summary_messages(work_packages))
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    ops_table = build_incident_table(tickets, status_updates)

    # DEV side: two tables.
    dev_task_table = build_work_package_table(dev_tasks)
    dev_incident_table = build_work_package_table(dev_incidents)

    dev_section = []
    dev_section.append("## DEV Side")
    dev_section.append("### Tasks")
    dev_section.append(dev_task_table)
    dev_section.append("### Incidents (referenced by GLPI)")
    dev_section.append(dev_incident_table)
    dev_section.append(dev_summary)

    text = (
        f"## OPS Side\n\n{ops_table}\n\n{ops_summary}\n\n"
        + "\n\n".join(dev_section)
    )

    return {
        "section": "summary",
        "data": {
            "tickets": len(tickets),
            "work_packages": len(work_packages),
            "dev_tasks": len(dev_tasks),
            "dev_incidents": len(dev_incidents),
        },
        "ai_text": text,
        "elapsed_ms": elapsed_ms,
    }


@router.post("/incident-analysis")
async def ai_incident_analysis():
    """Analyze the current GLPI incidents.
    Fetches all GLPI tickets, sends them to llama.cpp, and returns
    a focused analysis: what's recurring, common issues, and what
    to investigate first. No table — pure analysis.
    """
    start = time.perf_counter()
    tickets = await list_tickets()

    messages = build_incident_analysis_messages(tickets)
    text = await chat_completion(messages)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    return {
        "section": "incident_analysis",
        "data": {"ticket_count": len(tickets)},
        "ai_text": text,
        "elapsed_ms": elapsed_ms,
    }


@router.post("/report")
async def ai_report():
    """Generate the sprint report (last 2 weeks).
    Assembles a clean markdown report
    """
    start = time.perf_counter()
    tickets = await list_tickets()
    work_packages = await list_work_packages()

    # Keep only items from the last sprint window.
    tickets = _last_sprint_tickets(tickets)
    work_packages = _last_sprint_work_packages(work_packages)

    # Fetch each ticket's comments so the Status Update column is
    # accurate here too (resolved / handed to dev / pending).
    followups = await gather(
        *(get_ticket_followups(t.get("id")) for t in tickets)
    )
    followups_by_ticket = {
        t.get("id"): f for t, f in zip(tickets, followups)
    }
    dev_incidents, _ = split_work_packages(work_packages)
    status_updates = compute_status_updates(tickets, followups_by_ticket, dev_incidents)

    # Counts for the report header.
    incident_counts = _incident_counts(tickets)
    dev_counts = _dev_counts(work_packages)

    incident_table = build_incident_table(tickets, status_updates)
    dev_table = build_work_package_table(work_packages)

    # Two focused AI calls: incidents narrative + dev narrative.
    incident_text = await chat_completion(
        build_incident_report_messages(incident_table, incident_counts)
    )
    dev_text = await chat_completion(
        build_dev_report_messages(dev_table, dev_counts)
    )
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    # Assemble the final report in the clean format. Our two section headings
    text = (
        "# Project Status Report\n\n"
        f"# Sprint: {_sprint_label()}\n\n"
        f"## Incidents:\n\n"
        f"Opened: {incident_counts['opened']} | "
        f"Active: {incident_counts['active']} | "
        f"Resolved/Closed: {incident_counts['closed']}\n\n"
        f"{incident_table}\n\n"
        f"{incident_text}\n\n"
        f"## Stories and Tasks:\n\n"
        f"Opened: {dev_counts['opened']} | "
        f"Active: {dev_counts['active']} | "
        f"Closed: {dev_counts['closed']}\n\n"
        f"{dev_table}\n\n"
        f"{dev_text}"
    )

    return {
        "section": "report",
        "data": {
            "incidents": incident_counts,
            "dev": dev_counts,
        },
        "ai_text": text,
        "elapsed_ms": elapsed_ms,
    }


# ── helpers ────────────────────────────────────────────


def _last_sprint_tickets(tickets: list[dict]) -> list[dict]:
    """Keep tickets created within the last SPRINT_DAYS."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=SPRINT_DAYS)
    kept = []
    for t in tickets:
        d = t.get("date") or ""
        try:
            opened = datetime.fromisoformat(d)
        except ValueError:
            continue
        if opened >= cutoff:
            kept.append(t)
    return kept


def _last_sprint_work_packages(work_packages: list[dict]) -> list[dict]:
    """Keep work packages created within the last SPRINT_DAYS."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=SPRINT_DAYS)
    kept = []
    for wp in work_packages:
        d = wp.get("createdAt") or ""
        try:
            created = datetime.fromisoformat(d.replace("Z", "+00:00"))
        except ValueError:
            continue
        if created >= cutoff:
            kept.append(wp)
    return kept


def _incident_counts(tickets: list[dict]) -> dict:
    """Count opened / active / resolved for the incident list."""
    opened = len(tickets)
    closed = sum(
        1 for t in tickets
        if (t.get("status") or {}).get("name") in RESOLVED_STATUSES
    )
    return {
        "opened": opened,
        "active": opened - closed,
        "closed": closed,
    }


def _dev_counts(work_packages: list[dict]) -> dict:
    """Count opened / active / closed for the dev task list."""
    opened = len(work_packages)
    closed = sum(
        1 for wp in work_packages
        if (wp.get("_links", {}).get("status") or {}).get("title", "").lower() == "closed"
    )
    return {
        "opened": opened,
        "active": opened - closed,
        "closed": closed,
    }


def _sprint_label() -> str:
    """Build a sprint label, e.g. '#13 (Aug 03 - Aug 17)'.
    Sprint number is derived from the current date (14-day sprints).
    """
    now = datetime.now(timezone.utc)
    sprint_end = now.date()
    sprint_start = sprint_end - timedelta(days=SPRINT_DAYS - 1)
    sprint_num = _sprint_number(now)
    return f"#{sprint_num} ({sprint_start.strftime('%b %d')} - {sprint_end.strftime('%b %d')})"


def _sprint_number(now: datetime) -> int:
    """Compute a sprint number from the date (14-day sprints)."""
    epoch = datetime(2026, 1, 1, tzinfo=timezone.utc)
    days = (now - epoch).days
    return days // SPRINT_DAYS + 1
