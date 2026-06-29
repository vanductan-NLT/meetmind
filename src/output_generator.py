"""Generate HTML and PDF meeting notes from analysis result (in-memory, no disk writes)."""
import io
from datetime import date


_CSS = """
@page {
    size: A4;
    margin: 52px 62px 56px 62px;
}

body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.65;
    color: #1A1A2E;
    background: #FFFFFF;
    margin: 0;
    padding: 0;
}

/* ── Report header ─────────────────────────────────── */
.rh {
    padding-bottom: 13px;
    border-bottom: 2px solid #0F172A;
    margin-bottom: 26px;
}
.rh-title {
    font-size: 19pt;
    font-weight: bold;
    color: #0F172A;
    margin: 0 0 3px 0;
    letter-spacing: -0.3px;
}
.rh-meta {
    font-size: 9pt;
    color: #64748B;
    margin: 0;
}

/* ── Section ───────────────────────────────────────── */
.sec {
    margin-bottom: 26px;
}
.sec-label {
    font-size: 7.5pt;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #94A3B8;
    border-bottom: 1px solid #E2E8F0;
    padding-bottom: 5px;
    margin-bottom: 13px;
}

/* ── Summary ───────────────────────────────────────── */
.summary {
    font-size: 10.5pt;
    line-height: 1.72;
    color: #1E293B;
    background: #F8FAFC;
    border-left: 3px solid #2563EB;
    padding: 11px 15px;
}

/* ── Action items table ────────────────────────────── */
.at {
    width: 100%;
    border-collapse: collapse;
}
.at th {
    text-align: left;
    font-size: 7.5pt;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #64748B;
    background: #F1F5F9;
    padding: 7px 10px;
    border-bottom: 1.5px solid #CBD5E1;
}
.at td {
    padding: 9px 10px;
    border-bottom: 1px solid #F1F5F9;
    vertical-align: top;
    font-size: 10pt;
    color: #1E293B;
}
.at tr:last-child td {
    border-bottom: none;
}
.at-num {
    color: #94A3B8;
    font-size: 9pt;
    font-weight: bold;
}
.at-task {
    font-weight: bold;
    color: #0F172A;
}
.at-quote {
    font-style: italic;
    color: #64748B;
    font-size: 9pt;
    display: block;
    margin-top: 3px;
}
.at-badge {
    font-size: 7.5pt;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* ── Conflict items ────────────────────────────────── */
.ci {
    border: 1px solid #FECACA;
    background: #FFF8F8;
    padding: 11px 14px;
    margin-bottom: 9px;
}
.ci-topic {
    font-size: 10pt;
    font-weight: bold;
    color: #B91C1C;
    margin-bottom: 9px;
}
.ci-src {
    font-size: 7.5pt;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94A3B8;
    margin-bottom: 2px;
}
.ci-val {
    font-size: 10pt;
    font-weight: bold;
    color: #1E293B;
    margin-bottom: 2px;
}
.ci-quote {
    font-style: italic;
    font-size: 9pt;
    color: #6B7280;
}

/* ── Clear ─────────────────────────────────────────── */
.no-issues {
    background: #F0FDF4;
    border-left: 3px solid #16A34A;
    padding: 10px 14px;
    font-size: 10pt;
    color: #15803D;
    font-weight: bold;
}

/* ── Footer ────────────────────────────────────────── */
.footer {
    margin-top: 32px;
    padding-top: 9px;
    border-top: 1px solid #E2E8F0;
    font-size: 7.5pt;
    color: #94A3B8;
    text-align: center;
}
"""


def to_html(result: dict, title: str = "Meeting Notes") -> str:
    """Render analysis result as a professional self-contained HTML string."""
    today = date.today().strftime("%B %d, %Y")
    summary = result.get("summary", "")
    todos = result.get("todos", [])
    conflicts = result.get("conflicts", [])

    p = []
    p.append(f"<html><head><meta charset='utf-8'><style>{_CSS}</style></head><body>")

    # ── Header ──────────────────────────────────────────────────────────────
    p.append(
        f"<div class='rh'>"
        f"<div class='rh-title'>{title}</div>"
        f"<div class='rh-meta'>Generated {today} &nbsp;&bull;&nbsp; Confidential</div>"
        f"</div>"
    )

    # ── Executive Summary ────────────────────────────────────────────────────
    p.append("<div class='sec'>")
    p.append("<div class='sec-label'>Executive Summary</div>")
    p.append(f"<div class='summary'>{summary}</div>")
    p.append("</div>")

    # ── Action Items ─────────────────────────────────────────────────────────
    n_todos = len(todos)
    p.append("<div class='sec'>")
    p.append(f"<div class='sec-label'>Action Items &mdash; {n_todos} item{'s' if n_todos != 1 else ''}</div>")

    if todos:
        p.append(
            "<table class='at'>"
            "<thead><tr>"
            "<th style='width:4%'>#</th>"
            "<th style='width:39%'>Task</th>"
            "<th style='width:19%'>Assignee</th>"
            "<th style='width:16%'>Due Date</th>"
            "<th style='width:22%'>Source</th>"
            "</tr></thead>"
            "<tbody>"
        )
        for i, item in enumerate(todos, 1):
            assignee = item.get("assignee") or "&mdash;"
            deadline = item.get("deadline") or "&mdash;"
            quote = item.get("source_quote", "")
            ref = "Audio recording" if item.get("source_ref") == "audio" else "Reference document"
            p.append(
                f"<tr>"
                f"<td class='at-num'>{i}</td>"
                f"<td>"
                f"<span class='at-task'>{item.get('task', '')}</span>"
                f"<span class='at-quote'>&ldquo;{quote}&rdquo;</span>"
                f"</td>"
                f"<td>{assignee}</td>"
                f"<td>{deadline}</td>"
                f"<td><span class='at-badge'>{ref}</span></td>"
                f"</tr>"
            )
        p.append("</tbody></table>")
    else:
        p.append("<p style='color:#64748B; font-style:italic; margin:0;'>No action items identified.</p>")

    p.append("</div>")

    # ── Discrepancies ────────────────────────────────────────────────────────
    n_conf = len(conflicts)
    p.append("<div class='sec'>")
    p.append(f"<div class='sec-label'>Discrepancies &mdash; {n_conf} found</div>")

    if conflicts:
        for c in conflicts:
            p.append(
                f"<div class='ci'>"
                f"<div class='ci-topic'>{c.get('topic', '')}</div>"
                f"<table style='width:100%; border-collapse:collapse;'><tr>"
                f"<td style='width:50%; vertical-align:top; padding-right:14px;'>"
                f"<div class='ci-src'>Audio Recording</div>"
                f"<div class='ci-val'>{c.get('audio_value', '')}</div>"
                f"<div class='ci-quote'>&ldquo;{c.get('audio_quote', '')}&rdquo;</div>"
                f"</td>"
                f"<td style='width:50%; vertical-align:top; padding-left:14px;"
                f"border-left:1px solid #FECACA;'>"
                f"<div class='ci-src'>Reference Document</div>"
                f"<div class='ci-val'>{c.get('doc_value', '')}</div>"
                f"<div class='ci-quote'>&ldquo;{c.get('doc_quote', '')}&rdquo;</div>"
                f"</td>"
                f"</tr></table>"
                f"</div>"
            )
    else:
        p.append(
            "<div class='no-issues'>"
            "No discrepancies detected between the audio recording and the reference document."
            "</div>"
        )

    p.append("</div>")

    # ── Footer ───────────────────────────────────────────────────────────────
    p.append("<div class='footer'>MeetMind &nbsp;&bull;&nbsp; For internal use only</div>")
    p.append("</body></html>")

    return "\n".join(p)


def to_markdown(result: dict) -> str:
    """Render analysis result as clean markdown."""
    today = date.today().strftime("%B %d, %Y")
    lines = [
        "# Meeting Notes",
        f"*{today}*",
        "",
        "## Executive Summary",
        "",
        result.get("summary", ""),
        "",
    ]

    todos = result.get("todos", [])
    lines.append(f"## Action Items ({len(todos)})")
    lines.append("")
    if todos:
        for i, item in enumerate(todos, 1):
            assignee = item.get("assignee") or "—"
            deadline = item.get("deadline") or "—"
            ref = "Audio" if item.get("source_ref") == "audio" else "Document"
            lines.append(f"**{i}. {item.get('task', '')}**")
            lines.append(f"Assignee: {assignee} &nbsp;·&nbsp; Due: {deadline} &nbsp;·&nbsp; Source: {ref}")
            lines.append(f"> \"{item.get('source_quote', '')}\"")
            lines.append("")
    else:
        lines.append("*No action items identified.*")
        lines.append("")

    conflicts = result.get("conflicts", [])
    lines.append(f"## Discrepancies ({len(conflicts)})")
    lines.append("")
    if conflicts:
        for c in conflicts:
            lines.append(f"**{c.get('topic', '')}**")
            lines.append(f"- Audio: {c.get('audio_value', '')} — *\"{c.get('audio_quote', '')}\"*")
            lines.append(f"- Document: {c.get('doc_value', '')} — *\"{c.get('doc_quote', '')}\"*")
            lines.append("")
    else:
        lines.append("*No discrepancies detected.*")

    return "\n".join(lines)


def to_pdf(html: str) -> bytes:
    """Convert HTML string to PDF bytes using xhtml2pdf (pure-Python, Windows-safe)."""
    try:
        from xhtml2pdf import pisa
    except ImportError:
        raise RuntimeError("xhtml2pdf not installed. Run: pip install xhtml2pdf")

    buf = io.BytesIO()
    status = pisa.CreatePDF(html, dest=buf)
    if status.err:
        raise RuntimeError(f"PDF generation failed (xhtml2pdf error code {status.err}).")
    return buf.getvalue()
