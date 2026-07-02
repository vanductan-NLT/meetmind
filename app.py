"""MeetMind — AI-powered meeting notes.

Upload a meeting audio file + a reference document to generate:
  • Executive summary
  • Action items (assignee, deadline, source quote)
  • Discrepancy report (audio vs document)
Output rendered on screen and downloadable as PDF or Markdown.
"""
import os
import tempfile
import streamlit as st
from src.config import validate_keys, MAX_AUDIO_MB, MAX_DOC_MB, ALLOWED_AUDIO_EXT, ALLOWED_DOC_EXT

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MeetMind",
    page_icon="🧠",
    layout="centered",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Layout ─────────────────────────────────────────────── */
.block-container {
    padding-top: 2.25rem !important;
    padding-bottom: 3rem !important;
    max-width: 840px !important;
}

/* ── Typography ─────────────────────────────────────────── */
h1 {
    font-size: 1.85rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.03em !important;
    color: #0F172A !important;
    line-height: 1.2 !important;
    margin-bottom: 0.1rem !important;
}
h2, h3 {
    font-weight: 600 !important;
    letter-spacing: -0.015em !important;
    color: #1E293B !important;
}
[data-testid="stCaptionContainer"] p,
.stCaption p {
    font-size: 0.92rem !important;
    color: #64748B !important;
    margin-top: 0.1rem !important;
}

/* ── Primary button ─────────────────────────────────────── */
div[data-testid="stButton"] > button[kind="primary"] {
    background: #0F172A !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.93rem !important;
    letter-spacing: 0.02em !important;
    height: 2.75rem !important;
    transition: background 0.15s, box-shadow 0.15s, transform 0.1s !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover:not(:disabled) {
    background: #1E293B !important;
    box-shadow: 0 4px 16px rgba(15,23,42,0.22) !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stButton"] > button[kind="primary"]:disabled {
    background: #CBD5E1 !important;
    color: #94A3B8 !important;
}

/* ── Download button ─────────────────────────────────────── */
div[data-testid="stDownloadButton"] > button {
    background: #059669 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.93rem !important;
    letter-spacing: 0.02em !important;
    height: 2.75rem !important;
    transition: background 0.15s, box-shadow 0.15s, transform 0.1s !important;
}
div[data-testid="stDownloadButton"] > button:hover {
    background: #047857 !important;
    box-shadow: 0 4px 16px rgba(5,150,105,0.28) !important;
    transform: translateY(-1px) !important;
}

/* ── File uploader ───────────────────────────────────────── */
[data-testid="stFileUploaderDropzone"] {
    background: #F8FAFC !important;
    border: 1.5px dashed #CBD5E1 !important;
    border-radius: 10px !important;
    transition: border-color 0.2s, background 0.2s !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #93C5FD !important;
    background: #F0F9FF !important;
}

/* ── Bordered containers (cards) ─────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
    background: #FFFFFF !important;
}

/* ── Alerts / info boxes ─────────────────────────────────── */
[data-baseweb="notification"] {
    border-radius: 8px !important;
    border: none !important;
    font-size: 0.92rem !important;
    line-height: 1.65 !important;
}

/* ── Expander ────────────────────────────────────────────── */
details summary {
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    color: #94A3B8 !important;
}

/* ── Divider ─────────────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid #E2E8F0 !important;
    margin: 1.75rem 0 !important;
}

/* ── Status widget ───────────────────────────────────────── */
[data-testid="stStatus"] {
    border-radius: 8px !important;
}

/* ── Hide Streamlit chrome ───────────────────────────────── */
#MainMenu          { visibility: hidden !important; }
footer             { visibility: hidden !important; }
[data-testid="stToolbar"] { display: none !important; }

/* ── Hide auto-generated "XMB per file" label in uploader ── */
[data-testid="stFileUploaderDropzoneInstructions"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("MeetMind")
st.caption("Turn your meeting recordings into structured, actionable notes in seconds.")

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# ── API key validation ────────────────────────────────────────────────────────
try:
    validate_keys()
except ValueError as e:
    st.error(str(e))
    st.stop()

# ── File uploaders ────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    audio_files = st.file_uploader(
        "Meeting Recording",
        type=list(ALLOWED_AUDIO_EXT),
        accept_multiple_files=True,
    )
    st.caption("MP3, M4A, WAV · up to 60 min · 100 MB total")
with col2:
    doc_files = st.file_uploader(
        "Reference Document",
        type=list(ALLOWED_DOC_EXT),
        accept_multiple_files=True,
    )
    st.caption("PDF, DOCX, MD, TXT, JSON · 50 MB total")


def _check_total_size(files: list, label: str, limit_mb: int) -> bool:
    total = sum(f.size for f in files)
    if total > limit_mb * 1024 * 1024:
        mb = total / 1024 / 1024
        st.error(f"{label} total size {mb:.1f} MB exceeds the {limit_mb} MB limit.")
        return False
    return True


audio_ok = _check_total_size(audio_files, "Recording", MAX_AUDIO_MB) if audio_files else True
doc_ok = _check_total_size(doc_files, "Document", MAX_DOC_MB) if doc_files else True

st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)

# ── Generate button ───────────────────────────────────────────────────────────
generate = st.button(
    "Generate Meeting Notes",
    disabled=not (audio_files and doc_files and audio_ok and doc_ok),
    type="primary",
    use_container_width=True,
)

if generate:
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_paths, doc_paths = [], []

        for i, f in enumerate(audio_files):
            ext = os.path.splitext(f.name)[1]
            path = os.path.join(tmpdir, f"audio_{i}{ext}")
            with open(path, "wb") as fp:
                fp.write(f.read())
            audio_paths.append(path)

        for i, f in enumerate(doc_files):
            ext = os.path.splitext(f.name)[1]
            path = os.path.join(tmpdir, f"doc_{i}{ext}")
            with open(path, "wb") as fp:
                fp.write(f.read())
            doc_paths.append(path)

        st.session_state.pop("result", None)

        try:
            with st.status("Analyzing your meeting…", expanded=True) as status:
                st.write("Transcribing audio…")
                from src.audio_transcription import transcribe
                transcripts = []
                for path in audio_paths:
                    transcripts.append(transcribe(path))
                transcript = "\n\n---\n\n".join(transcripts)
                st.write(f"✓ {len(audio_paths)} audio file{'s' if len(audio_paths) > 1 else ''} transcribed")

                st.write("Reading document…")
                from src.document_extraction import extract
                doc_texts = []
                for path in doc_paths:
                    doc_texts.append(extract(path))
                doc_text = "\n\n---\n\n".join(doc_texts)
                st.write(f"✓ {len(doc_paths)} document{'s' if len(doc_paths) > 1 else ''} processed")

                st.write("Analyzing content…")
                from src.content_analysis import analyze
                analysis = analyze(transcript, doc_text)
                n_todos = len(analysis.get("todos", []))
                n_conflicts = len(analysis.get("conflicts", []))
                st.write(f"✓ {n_todos} action item{'s' if n_todos != 1 else ''} · {n_conflicts} discrepanc{'ies' if n_conflicts != 1 else 'y'}")

                st.write("Preparing notes…")
                from src.output_generator import to_html, to_markdown, to_pdf
                html = to_html(analysis)
                pdf_bytes = to_pdf(html)
                markdown = to_markdown(analysis)
                st.write("✓ Notes ready")

                status.update(label="Done", state="complete", expanded=False)

            st.session_state["result"] = {
                "transcript": transcript,
                "doc_text": doc_text,
                "analysis": analysis,
                "markdown": markdown,
                "html": html,
                "pdf_bytes": pdf_bytes,
            }

        except FileNotFoundError as e:
            st.error(f"File error: {e}")
        except ValueError as e:
            st.error(f"Input error: {e}")
        except RuntimeError as e:
            st.error(f"Pipeline error: {e}")

# ── Results ───────────────────────────────────────────────────────────────
if st.session_state.get("result"):
    result = st.session_state["result"]
    analysis = result["analysis"]
    todos = analysis.get("todos", [])
    conflicts = analysis.get("conflicts", [])

    dl_pdf, dl_md = st.columns(2)
    with dl_pdf:
        st.download_button(
            label="Download PDF Report",
            data=result["pdf_bytes"],
            file_name="meeting_notes.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )
    with dl_md:
        st.download_button(
            label="Download Markdown",
            data=result["markdown"],
            file_name="meeting_notes.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.divider()

    # ── Summary ───────────────────────────────────────────────────────────
    st.subheader("Executive Summary")
    st.info(analysis.get("summary", ""))

    # ── Action Items ──────────────────────────────────────────────────────
    st.subheader(f"Action Items — {len(todos)}")

    if todos:
        for item in todos:
            assignee = item.get("assignee") or "—"
            deadline = item.get("deadline") or "—"
            source = "Audio" if item.get("source_ref") == "audio" else "Document"
            with st.container(border=True):
                left, right = st.columns([7, 3])
                with left:
                    st.markdown(f"**{item.get('task', '')}**")
                    st.caption(f'"{item.get("source_quote", "")}"')
                with right:
                    st.markdown(
                        f"<div style='font-size:0.82rem; color:#64748B; line-height:1.8;'>"
                        f"<b style='color:#1E293B'>Assignee</b><br>{assignee}<br>"
                        f"<b style='color:#1E293B'>Due</b><br>{deadline}<br>"
                        f"<b style='color:#1E293B'>Source</b><br>{source}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
    else:
        st.caption("No action items identified.")

    # ── Discrepancies ─────────────────────────────────────────────────────
    st.subheader(f"Discrepancies — {len(conflicts)}")

    if conflicts:
        for c in conflicts:
            with st.container(border=True):
                st.markdown(
                    f"<span style='font-weight:700; color:#B91C1C;'>"
                    f"{c.get('topic', '')}</span>",
                    unsafe_allow_html=True,
                )
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(
                        "<span style='font-size:0.78rem; font-weight:700; "
                        "text-transform:uppercase; letter-spacing:0.07em; "
                        "color:#94A3B8;'>Audio Recording</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**{c.get('audio_value', '')}**")
                    st.caption(f'"{c.get("audio_quote", "")}"')
                with col_b:
                    st.markdown(
                        "<span style='font-size:0.78rem; font-weight:700; "
                        "text-transform:uppercase; letter-spacing:0.07em; "
                        "color:#94A3B8;'>Reference Document</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**{c.get('doc_value', '')}**")
                    st.caption(f'"{c.get("doc_quote", "")}"')
    else:
        st.success("No discrepancies detected between the recording and reference document.")

    # ── Raw data (collapsible) ─────────────────────────────────────────────
    st.divider()
    with st.expander("View transcript"):
        st.text(result["transcript"])
    with st.expander("View document text"):
        st.text(result["doc_text"])
