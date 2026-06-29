"""Generate HTML and PDF meeting notes from analysis result (in-memory, no disk writes)."""
import io
from datetime import date
import markdown as md_lib


_CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       max-width: 800px; margin: 40px auto; padding: 0 24px; color: #1a1a1a; }
h1 { font-size: 1.8em; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; }
h2 { font-size: 1.2em; margin-top: 32px; color: #2c2c2c; }
.date { color: #888; font-size: 0.9em; margin-top: -4px; }
.summary { background: #f8f8f8; border-left: 4px solid #4a90d9;
           padding: 12px 16px; border-radius: 4px; line-height: 1.6; }
.todo-item { margin-bottom: 14px; padding: 10px 14px;
             border: 1px solid #e8e8e8; border-radius: 6px; }
.todo-task { font-weight: 600; font-size: 1em; }
.todo-meta { color: #666; font-size: 0.85em; margin-top: 4px; }
.todo-quote { border-left: 3px solid #ccc; padding-left: 10px;
              color: #555; font-style: italic; font-size: 0.88em; margin-top: 6px; }
.conflict-box { background: #fff8e1; border: 1px solid #ffe082;
                border-radius: 6px; padding: 14px; margin-bottom: 14px; }
.conflict-topic { font-weight: 700; color: #b45309; margin-bottom: 8px; }
.conflict-col { display: inline-block; width: 48%; vertical-align: top; }
.conflict-label { font-size: 0.8em; font-weight: 700; text-transform: uppercase;
                  color: #888; margin-bottom: 4px; }
.conflict-value { font-weight: 600; margin-bottom: 4px; }
.conflict-quote { font-style: italic; color: #666; font-size: 0.85em; }
.no-conflicts { color: #4caf50; font-style: italic; }
"""


def to_html(result: dict, title: str = "Meeting Notes") -> str:
    """Render analysis result as a self-contained HTML string."""
    today = date.today().strftime("%B %d, %Y")
    summary = result.get("summary", "")
    todos = result.get("todos", [])
    conflicts = result.get("conflicts", [])

    parts = [
        f"<html><head><meta charset='utf-8'><style>{_CSS}</style></head><body>",
        f"<h1>{title}</h1>",
        f"<p class='date'>{today}</p>",
        "<h2>📝 Summary</h2>",
        f"<div class='summary'>{summary}</div>",
        "<h2>✅ To-do List</h2>",
    ]

    if todos:
        for item in todos:
            assignee = item.get("assignee") or "—"
            deadline = item.get("deadline") or "—"
            quote = item.get("source_quote", "")
            ref = "🎙 Audio" if item.get("source_ref") == "audio" else "📄 Doc"
            parts.append(
                f"<div class='todo-item'>"
                f"<div class='todo-task'>☐ {item.get('task', '')}</div>"
                f"<div class='todo-meta'>👤 {assignee} &nbsp;|&nbsp; 📅 {deadline}</div>"
                f"<div class='todo-quote'>{ref}: &ldquo;{quote}&rdquo;</div>"
                f"</div>"
            )
    else:
        parts.append("<p><em>No action items found.</em></p>")

    parts.append("<h2>⚠️ Conflict Warning</h2>")

    if conflicts:
        for c in conflicts:
            parts.append(
                f"<div class='conflict-box'>"
                f"<div class='conflict-topic'>⚠ {c.get('topic', '')}</div>"
                f"<div class='conflict-col'>"
                f"  <div class='conflict-label'>🎙 Audio says</div>"
                f"  <div class='conflict-value'>{c.get('audio_value', '')}</div>"
                f"  <div class='conflict-quote'>&ldquo;{c.get('audio_quote', '')}&rdquo;</div>"
                f"</div>"
                f"<div class='conflict-col'>"
                f"  <div class='conflict-label'>📄 Document says</div>"
                f"  <div class='conflict-value'>{c.get('doc_value', '')}</div>"
                f"  <div class='conflict-quote'>&ldquo;{c.get('doc_quote', '')}&rdquo;</div>"
                f"</div>"
                f"</div>"
            )
    else:
        parts.append("<p class='no-conflicts'>✓ No conflicts detected between audio and document.</p>")

    parts.append("</body></html>")
    return "\n".join(parts)


def to_markdown(result: dict) -> str:
    """Render analysis result as markdown (used for Streamlit preview)."""
    today = date.today().strftime("%Y-%m-%d")
    lines = [f"# Meeting Notes — {today}", "", "## 📝 Summary", "", result.get("summary", ""), ""]

    todos = result.get("todos", [])
    lines.append("## ✅ To-do List")
    lines.append("")
    if todos:
        for item in todos:
            assignee = item.get("assignee") or "—"
            deadline = item.get("deadline") or "—"
            ref = "🎙" if item.get("source_ref") == "audio" else "📄"
            lines.append(f"- [ ] **{item.get('task', '')}**")
            lines.append(f"  - 👤 {assignee} | 📅 {deadline}")
            lines.append(f"  - {ref} *\"{item.get('source_quote', '')}\"*")
            lines.append("")
    else:
        lines.append("*No action items found.*")
        lines.append("")

    conflicts = result.get("conflicts", [])
    lines.append("## ⚠️ Conflict Warning")
    lines.append("")
    if conflicts:
        for c in conflicts:
            lines.append(f"**⚠ {c.get('topic', '')}**")
            lines.append(f"- 🎙 Audio: {c.get('audio_value', '')} — *\"{c.get('audio_quote', '')}\"*")
            lines.append(f"- 📄 Doc: {c.get('doc_value', '')} — *\"{c.get('doc_quote', '')}\"*")
            lines.append("")
    else:
        lines.append("✓ No conflicts detected.")

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
