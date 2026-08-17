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


# Builds the prompt for the OPS side of the summary — focuses only on the
# IT support ticket situation (embeds the ticket list + their status updates,
# asks for a short summary). `status_updates` maps ticket id -> a short note
# like "resolved", "handed to dev", or "pending".
def build_ops_summary_messages(
    tickets: list[dict],
    status_updates: dict | None = None,
) -> list[dict]:
    """Prompt for the "OPS Side" summary.
    Input: the GLPI ticket list (+ optional status updates).
    Output: a message list asking for a short IT-support summary.
    """
    status_updates = status_updates or {}
    system = (
        "You are a concise IT operations analyst. "
        "Summarize ONLY the IT support side of the project in plain human language. "
        "No markdown tables, just 2-4 clear sentences. "
        "Differentiate tickets by their Status Update (resolved / handed to dev / pending)."
    )
    user = f"""
        Here is the current IT support data (GLPI tickets):

        {_format_tickets_with_updates(tickets, status_updates)}

        Write a short OPS summary covering:
        - How the support workload looks
        - What the main issue areas are
        - How many are resolved, handed to dev, or still pending
        - Anything that stands out
    """
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# Builds the prompt for the DEV side of the summary — focuses ONLY on the
# OpenProject work-package situation (embeds the task list, asks for a short summary).
def build_dev_summary_messages(work_packages: list[dict]) -> list[dict]:
    """Prompt for the "DEV Side" summary.
    Input: the OpenProject work-package list.
    Output: a message list asking for a short development summary.
    """
    system = (
        "You are a concise development lead. "
        "Summarize ONLY the development side of the project in plain human language. "
        "No markdown tables, just 2-4 clear sentences."
    )
    user = f"""
        Here is the current development data (OpenProject work packages):

        {_format_work_packages(work_packages)}

        Write a short DEV summary covering:
        - How the development work looks
        - What the main tasks/stories are
        - Anything that stands out
    """
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# Builds a markdown table of the OpenProject work packages
# (ID, subject, type, status) so it is always correctly formatted.
def build_work_package_table(work_packages: list[dict]) -> str:
    """Turn the work-package list into a markdown table.
    Columns: ID | Subject | Type | Status
    """
    rows = []
    for wp in work_packages[:30]:
        wp_id = wp.get("id")
        subject = (wp.get("subject") or "(no subject)").replace("|", "\\|")
        wp_type = (wp.get("_links", {}).get("type") or {}).get("title", "?")
        status = (wp.get("_links", {}).get("status") or {}).get("title", "?")
        rows.append(f"| {wp_id} | {subject} | {wp_type} | {status} |")

    header = "| ID | Subject | Type | Status |"
    sep = "|----|---------|------|--------|"
    table = "\n".join([header, sep] + rows)
    return table if rows else "(no work packages)"


# Builds a markdown table of the OpenProject INCIDENT tasks — those whose subject
# references a GLPI incident like "[BUG] [INC #7] ...". Same columns as tasks.
def build_incident_work_package_table(incident_wps: list[dict]) -> str:
    """Turn the incident work-package list into a markdown table.
    Columns: ID | Subject | Type | Status
    """
    return build_work_package_table(incident_wps)


# Splits the OpenProject work packages into two lists:
#   - incidents: subjects that reference a GLPI incident ("[INC #N]")
#   - tasks:     everything else (features/stories)
def split_work_packages(work_packages: list[dict]) -> tuple[list[dict], list[dict]]:
    """Return (incidents, tasks)."""
    incidents = []
    tasks = []
    for wp in work_packages:
        subject = wp.get("subject") or ""
        if "[INC #" in subject:
            incidents.append(wp)
        else:
            tasks.append(wp)
    return incidents, tasks


# Builds a {ticket_id: "handed to dev: <status>"} map from the incident work
# packages. Used on the OPS side to show whether/when an incident went to dev.
def dev_status_by_incident(incident_wps: list[dict]) -> dict[int, str]:
    """Map GLPI ticket id -> short status-update text for the OPS table."""
    result = {}
    for wp in incident_wps:
        subject = wp.get("subject") or ""
        # Extract the incident id, e.g. "[INC #7]" -> 7
        marker = subject.split("[INC #", 1)[-1].split("]", 1)[0]
        try:
            inc_id = int(marker.strip())
        except ValueError:
            continue
        status = (wp.get("_links", {}).get("status") or {}).get("title", "?")
        result[inc_id] = f"handed to dev: {status}"
    return result


# Builds a markdown table of the incidents (ID, short description, GLPI status,
# status update, opened date) so it is always correctly formatted.
# `status_updates` maps a GLPI ticket ID -> a short "Status Update" note
# (e.g. "resolved", "waiting for dev work", "handed to dev: In progress").
def build_incident_table(tickets: list[dict], status_updates: dict | None = None) -> str:
    """Turn the GLPI ticket list into a markdown table.
    Columns: Incident ID | Description (short) | GLPI Status | Status Update | Opened
    """
    status_updates = status_updates or {}
    rows = []
    for t in tickets[:30]:
        t_id = t.get("id")
        name = (t.get("name") or "(no title)").replace("|", "\\|")
        content = (t.get("content") or "")
        # Short description = title, or first ~60 chars of content.
        desc = name if name != "(no title)" else (content[:60] + ("..." if len(content) > 60 else ""))
        glpi_status = (t.get("status") or {}).get("name", "?")
        opened = (t.get("date") or "")[:10]

        status_update = status_updates.get(t_id, "waiting for dev work")

        rows.append(f"| {t_id} | {desc} | {glpi_status} | {status_update} | {opened} |")

    header = "| ID | Description | GLPI Status | Status Update | Opened |"
    sep = "|----|-------------|-------------|---------------|--------|"
    table = "\n".join([header, sep] + rows)
    return table if rows else "(no tickets)"


# Computes the "Status Update" text for each ticket by reading the GLPI status
# and the ticket's comments (followups). No AI — deterministic rules:
#   - GLPI status Solved/Closed            -> "resolved"
#   - comments mention a fix               -> "resolved"
#   - comments mention a dev handoff       -> "handed to dev"
#   - comments mention investigation       -> "under investigation"
#   - comments ask the user for input      -> "waiting on user"
#   - OpenProject task references [INC #N] -> "handed to dev: <dev status>"
#   - otherwise (no useful comment)        -> "pending"
def compute_status_updates(
    tickets: list[dict],
    followups_by_ticket: dict[int, list[dict]],
    dev_incidents: list[dict],
) -> dict[int, str]:
    """Map GLPI ticket id -> short status-update text for the OPS table."""
    dev_map = dev_status_by_incident(dev_incidents)
    updates = {}
    for t in tickets:
        t_id = t.get("id")
        glpi_status = (t.get("status") or {}).get("name", "")

        # 1) Already solved/closed in GLPI -> obvious, it's fixed.
        # unless marked as invalid, but thats detail for future
        if glpi_status.lower() in {"solved", "closed", "resolved"}:
            updates[t_id] = "resolved"
            continue

        # 2) Otherwise, summarize from the comment context.
        hint = _followup_hint(followups_by_ticket.get(t_id, []))

        # 3) OpenProject task references this incident.
        dev_status = dev_map.get(t_id)

        if hint:
            updates[t_id] = hint
        elif dev_status:
            updates[t_id] = dev_status
        else:
            # No comment, no dev task -> nothing has been done yet.
            updates[t_id] = "pending"
    return updates


# Scans a ticket's followups and returns a short, context-based status note.
# The checks run most-specific -> least-specific so "fixed" wins over "dev".
def _followup_hint(followups: list[dict]) -> str | None:
    text = " ".join(
        (f.get("item") or {}).get("content", "") for f in followups
    )
    text_lower = _clean_html(text).lower()
    if not text_lower.strip():
        return None

    # Resolved: clearly fixed or closed.
    if any(k in text_lower for k in ("fixed", "resolved", "solved", "closed", "has been fixed")):
        return "resolved"

    # Handed to development / engineering team.
    if any(
        k in text_lower
        for k in ("handed", "informed the dev", "informed the development", "handed to dev",
                  "escalated to", "development team", "engineering team", "working on the fix",
                  "developers are", "developers will", "assigned to the dev")
    ):
        return "handed to dev"

    # Under investigation / analysis.
    if any(k in text_lower for k in ("investigat", "analyz", "examining", "looking into",
                                      "we are checking", "we will check", "reproduc")):
        return "under investigation"

    # Waiting on the user for more information.
    if any(k in text_lower for k in ("can you provide", "please provide", "please share",
                                      "need more", "we need", "waiting for your", "awaiting your")):
        return "waiting on user"

    # Fall back to the first short, clean sentence of the comment.
    sentence = _first_sentence(text)
    if sentence:
        return sentence[:60] + ("..." if len(sentence) > 60 else "")
    return None


# Removes HTML tags so comment text reads cleanly.
def _clean_html(text: str) -> str:
    import re

    return re.sub(r"<[^>]+>", " ", text)


# Returns the first sentence of a text (strips HTML first).
def _first_sentence(text: str) -> str:
    clean = " ".join(_clean_html(text).split())
    if not clean:
        return ""
    for sep in (". ", "! ", "? ", "\n"):
        if sep in clean:
            return clean.split(sep)[0] + sep.strip()
    return clean


# Builds the prompt for incident analysis by embedding the GLPI ticket list
# into a message pair that asks llama.cpp to find common/recurring themes.
def build_incident_analysis_messages(tickets: list[dict]) -> list[dict]:
    """Prompt for "Incident Analysis"
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


# Builds the prompt for the INCIDENT part of the sprint report. The AI writes
# a summary analysis, suggestions, and risks for the incident workload.
def build_incident_report_messages(
    incident_table: str,
    incident_counts: dict,
) -> list[dict]:
    """Prompt for the "Incidents" section of the sprint report."""
    system = (
        "You are an IT operations analyst writing the Incidents section "
        "of a sprint report. Be factual and concise based ONLY on the data given. "
        "Do not repeat the data as tables. Use markdown. "
        "Start each label with a bold title, e.g. '**AI Summary:**', "
        "'**Risks:**', '**Actions to take:**', followed by your text or bullets."
    )
    user = f"""
        Sprint incidents data:

        Opened: {incident_counts.get('opened', 0)} | Active: {incident_counts.get('active', 0)} | Resolved/Closed: {incident_counts.get('closed', 0)}

        Incidents:
        {incident_table}

        Write the Incidents section:
        1. '**AI Summary:**' followed by 2-3 sentences analyzing the incidents in this sprint (what happened, common themes).
        2. '**Risks:**' followed by 1-2 bullet points of the biggest risks.
        3. '**Actions to take:**' followed by 1-2 bullet points of recommended actions.
    """
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# Builds the prompt for the DEV part of the sprint report. The AI writes
# a summary and risks for the stories/tasks workload.
def build_dev_report_messages(
    dev_table: str,
    dev_counts: dict,
) -> list[dict]:
    """Prompt for the "Stories and Tasks" section of the sprint report."""
    system = (
        "You are a development lead writing the Stories and Tasks section "
        "of a sprint report. Be factual and concise based ONLY on the data given. "
        "Do not repeat the data as tables. Use markdown. "
        "Start each label with a bold title, e.g. '**AI Summary:**', "
        "'**Risks:**', '**Actions to take:**', followed by your text or bullets."
    )
    user = f"""
        Sprint development data:

        Opened: {dev_counts.get('opened', 0)} | Active: {dev_counts.get('active', 0)} | Closed: {dev_counts.get('closed', 0)}

        Stories and Tasks:
        {dev_table}

        Write the Stories and Tasks section:
        1. '**AI Summary:**' followed by 2-3 sentences analyzing the development work in this sprint.
        2. '**Risks:**' followed by 1-2 bullet points of the biggest risks.
        3. '**Actions to take:**' followed by 1-2 bullet points of recommended actions.
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


# Like _format_tickets but also appends the Status Update note
# (resolved / handed to dev / pending) for each ticket.
def _format_tickets_with_updates(
    tickets: list[dict],
    status_updates: dict | None = None,
) -> str:
    """Condense tickets including their Status Update."""
    status_updates = status_updates or {}
    lines = []
    for t in tickets[:30]:  # cap to avoid overflowing context
        t_id = t.get("id")
        name = t.get("name") or "(no title)"
        content = (t.get("content") or "")[:300]
        status = (t.get("status") or {}).get("name", "?")
        update = status_updates.get(t_id, "pending")
        lines.append(f"- [{status}] #{t_id} {name}: {content} (Status Update: {update})")
    return "\n".join(lines) if lines else "(no tickets)"


# Condenses the work-package list to "status: type: subject" lines (capped at 30)
# so the prompt stays small enough to fit the model's context window.
def _format_work_packages(work_packages: list[dict]) -> str:
    """Condense a list of work packages to the fields the AI needs."""
    lines = []
    for wp in work_packages[:30]:  # cap to avoid overflowing context
        subject = wp.get("subject") or "(no subject)"
        wp_type = (wp.get("_links", {}).get("type") or {}).get("title", "?")
        status = (wp.get("_links", {}).get("status") or {}).get("title", "?")
        lines.append(f"- [{status}] {wp_type}: {subject}")
    return "\n".join(lines) if lines else "(no work packages)"
