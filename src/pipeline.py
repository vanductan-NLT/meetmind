"""Orchestrate the full MeetMind pipeline: audio + doc → transcript + analysis → PDF."""
from src.audio_transcription import transcribe
from src.slide_extraction import extract
from src.content_analysis import analyze
from src.output_generator import to_html, to_markdown, to_pdf


def run(audio_path: str, doc_path: str) -> dict:
    """Run the end-to-end pipeline.

    Returns:
        dict with keys: transcript, doc_text, analysis, markdown, html, pdf_bytes
    Raises:
        RuntimeError / FileNotFoundError with user-friendly messages at each step.
    """
    transcript = transcribe(audio_path)
    doc_text = extract(doc_path)
    analysis = analyze(transcript, doc_text)
    html = to_html(analysis)
    pdf_bytes = to_pdf(html)
    markdown = to_markdown(analysis)

    return {
        "transcript": transcript,
        "doc_text": doc_text,
        "analysis": analysis,
        "markdown": markdown,
        "html": html,
        "pdf_bytes": pdf_bytes,
    }
