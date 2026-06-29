"""MeetMind — Streamlit demo app.

Upload a meeting audio file + a reference document to generate:
  • Meeting summary
  • To-do list (task, assignee, deadline, source quote)
  • Conflict warnings (discrepancies between audio and document)
Output is rendered on screen and downloadable as PDF.
"""
import os
import tempfile
import streamlit as st
from src.config import validate_keys, MAX_FILE_MB, ALLOWED_AUDIO_EXT, ALLOWED_DOC_EXT
from src.pipeline import run

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MeetMind",
    page_icon="🧠",
    layout="centered",
)

st.title("🧠 MeetMind")
st.caption("Multimodal meeting notes — summary · to-do · conflict detection")

# ── API key validation ────────────────────────────────────────────────────────
try:
    validate_keys()
except ValueError as e:
    st.error(str(e))
    st.stop()

# ── File uploaders ────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    audio_file = st.file_uploader(
        "🎙 Meeting audio",
        type=list(ALLOWED_AUDIO_EXT),
        help="MP3, M4A, or WAV — recommended under 10 min for demo",
    )
with col2:
    doc_file = st.file_uploader(
        "📄 Reference document",
        type=list(ALLOWED_DOC_EXT),
        help="PDF, DOCX, MD, or TXT — slides or meeting docs",
    )

# ── File size guard ───────────────────────────────────────────────────────────
def _check_size(uploaded, label: str) -> bool:
    if uploaded and uploaded.size > MAX_FILE_MB * 1024 * 1024:
        st.error(f"{label} exceeds {MAX_FILE_MB} MB limit ({uploaded.size // (1024*1024)} MB uploaded).")
        return False
    return True

audio_ok = _check_size(audio_file, "Audio file")
doc_ok = _check_size(doc_file, "Document file")

# ── Generate button ───────────────────────────────────────────────────────────
generate = st.button(
    "⚡ Generate Meeting Notes",
    disabled=not (audio_file and doc_file and audio_ok and doc_ok),
    type="primary",
    use_container_width=True,
)

if generate:
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save uploads to temp files
        audio_ext = os.path.splitext(audio_file.name)[1]
        doc_ext = os.path.splitext(doc_file.name)[1]
        audio_path = os.path.join(tmpdir, f"audio{audio_ext}")
        doc_path = os.path.join(tmpdir, f"document{doc_ext}")

        with open(audio_path, "wb") as f:
            f.write(audio_file.read())
        with open(doc_path, "wb") as f:
            f.write(doc_file.read())

        # ── Run pipeline with step-by-step status ────────────────────────────
        result = None
        status_placeholder = st.empty()

        try:
            with st.status("Running pipeline…", expanded=True) as status:
                st.write("🎙 Transcribing audio (ElevenLabs Scribe)…")
                from src.audio_transcription import transcribe
                transcript = transcribe(audio_path)
                st.write(f"✓ Transcript: {len(transcript.split())} words")

                st.write("📄 Extracting document text (MarkItDown)…")
                from src.slide_extraction import extract
                doc_text = extract(doc_path)
                st.write(f"✓ Document: {len(doc_text.split())} words")

                st.write("🤖 Analyzing with DeepSeek (summary + to-do + conflicts)…")
                from src.content_analysis import analyze
                analysis = analyze(transcript, doc_text)
                n_todos = len(analysis.get("todos", []))
                n_conflicts = len(analysis.get("conflicts", []))
                st.write(f"✓ {n_todos} task(s) · {n_conflicts} conflict(s) found")

                st.write("📑 Building PDF…")
                from src.output_generator import to_html, to_markdown, to_pdf
                html = to_html(analysis)
                pdf_bytes = to_pdf(html)
                markdown = to_markdown(analysis)
                st.write(f"✓ PDF ready ({len(pdf_bytes) // 1024} KB)")

                status.update(label="✅ Done!", state="complete", expanded=False)

            result = {
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
    if result:
        analysis = result["analysis"]
        todos = analysis.get("todos", [])
        conflicts = analysis.get("conflicts", [])

        # Download button at top
        st.download_button(
            label="⬇️ Download PDF",
            data=result["pdf_bytes"],
            file_name="meeting_notes.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )

        st.divider()

        # ── Summary ───────────────────────────────────────────────────────────
        st.subheader("📝 Summary")
        st.info(analysis.get("summary", ""))

        # ── To-do list ────────────────────────────────────────────────────────
        st.subheader(f"✅ To-do List ({len(todos)} item{'s' if len(todos) != 1 else ''})")
        if todos:
            for item in todos:
                assignee = item.get("assignee") or "—"
                deadline = item.get("deadline") or "—"
                ref_icon = "🎙" if item.get("source_ref") == "audio" else "📄"
                with st.container(border=True):
                    st.markdown(f"**☐ {item.get('task', '')}**")
                    st.caption(f"👤 {assignee}  ·  📅 {deadline}")
                    st.markdown(f"> {ref_icon} *\"{item.get('source_quote', '')}\"*")
        else:
            st.write("*No action items found.*")

        # ── Conflict Warning ──────────────────────────────────────────────────
        st.subheader(f"⚠️ Conflict Warning ({len(conflicts)})")
        if conflicts:
            for c in conflicts:
                with st.container(border=True):
                    st.markdown(f"**⚠ {c.get('topic', '')}**")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("**🎙 Audio says:**")
                        st.markdown(f"`{c.get('audio_value', '')}`")
                        st.caption(f"*\"{c.get('audio_quote', '')}\"*")
                    with col_b:
                        st.markdown("**📄 Document says:**")
                        st.markdown(f"`{c.get('doc_value', '')}`")
                        st.caption(f"*\"{c.get('doc_quote', '')}\"*")
        else:
            st.success("✓ No conflicts detected between audio and document.")

        # ── Raw transcript (collapsible) ──────────────────────────────────────
        with st.expander("📃 View raw transcript"):
            st.text(result["transcript"])
        with st.expander("📋 View document text"):
            st.text(result["doc_text"])
