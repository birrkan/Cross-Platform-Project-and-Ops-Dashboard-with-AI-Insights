# ─────────────────────────────────────────────────────────
# services/prompts.py — AI prompt templates
# ─────────────────────────────────────────────────────────
# All the prompts the AI endpoints use, kept in one place so
# they are easy to tweak without touching endpoint logic.
#
# Each prompt is a function that takes the gathered data (dicts
# from GLPI / OpenProject) and returns a ready-to-send message
# list for llama.cpp.
# ─────────────────────────────────────────────────────────


# Builds the prompt for the project-status summary by embedding GLPI + OpenProject stats
# into a system/user message pair that asks llama.cpp for a short human-language summary.
def build_summary_messages(ticket_stats: dict, wp_stats: dict) -> list[dict]:
    """Prompt for the "Project Status Summary".

    Input: the stats dicts from GLPI and OpenProject.
    Output: a message list asking for a human-language status.
    """
    system = (
        "You are a concise IT operations analyst. "
        "Summarize the current state of a project in plain human language. "
        "No markdown tables, just 3-5 clear sentences."
    )
    user = f"""
        Here is the current data from our systems.

        === IT Support (GLPI tickets) ===
        {_format_dict(ticket_stats)}

        === Development (OpenProject work packages) ===
        {_format_dict(wp_stats)}

        Write a short project status summary covering:
        - How the IT support workload looks
        - How the development work looks
        - Anything that stands out (worries, imbalances, busy areas)
    """
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# Builds the prompt for incident analysis by embedding the GLPI ticket list
# into a message pair that asks llama.cpp to find common/recurring themes.
def build_incident_analysis_messages(tickets: list[dict]) -> list[dict]:
    """Prompt for "Incident Analysis".

    Input: the raw list of GLPI tickets.
    Output: a message list asking for an incident analysis.
    """
    system = (
        "You are an incident analyst. Read the tickets and describe "
        "what the incidents have in common, which are recurring, and "
        "what the overall incident picture looks like. Be concise."
    )
    user = f"""
Here are the latest IT support tickets:

{_format_tickets(tickets)}

Analyze the incidents:
- What kind of issues are they?
- Which ones appear repeatedly (recurring themes)?
- What would you recommend investigating first?
"""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# Builds the prompt for the structured "Company Status" report by embedding GLPI + OpenProject
# stats into a message pair that instructs llama.cpp to follow the exact MVP report format.
def build_report_messages(ticket_stats: dict, wp_stats: dict) -> list[dict]:
    """Prompt for the structured "Company Status" report.

    Input: the stats dicts from GLPI and OpenProject.
    Output: a message list asking for the exact MVP report format.
    """
    system = (
        "You generate an operations status report. "
        "Follow the exact structure given by the user. "
        "Use plain text with a '─' separator line. "
        "Keep each section short and factual based ONLY on the data provided."
    )
    user = f"""
        Generate a status report in exactly this format:

        Company Status
        ────────────────────────
        IT Support
        Open incidents: <number>

        Main issues: <one short line>

        AI Summary: <1-2 sentences>
        ────────────────────────
        Development
        Active tasks: <number>

        Tasks summary: <one short line>

        Sprint progress: <percentage if derivable, else 'N/A'>

        AI Summary: <1-2 sentences>
        ────────────────────────
        Risks
        <bullet list of 2-4 risks derived from the data>

        Here is the data:

        === IT Support (GLPI tickets) ===
        {_format_dict(ticket_stats)}

        === Development (OpenProject work packages) ===
        {_format_dict(wp_stats)}

        Produce the report now.
    """
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# ── helpers ────────────────────────────────────────────


# Pretty-prints a dict as indented JSON so it reads well inside a prompt.
def _format_dict(data: dict) -> str:
    """Pretty-print a dict for inclusion in a prompt."""
    import json

    return json.dumps(data, indent=2, default=str)


# Condenses the ticket list to "status: title: content" lines (capped at 30)
# so the prompt stays small enough to fit the model's context window.
def _format_tickets(tickets: list[dict]) -> str:
    """Condense a list of tickets to the fields the AI needs."""
    lines = []
    for t in tickets[:30]:  # cap to avoid overflowing context
        name = t.get("name") or "(no title)"
        content = (t.get("content") or "")[:300]
        status = (t.get("status") or {}).get("name", "?")
        lines.append(f"- [{status}] {name}: {content}")
    return "\n".join(lines) if lines else "(no tickets)"
