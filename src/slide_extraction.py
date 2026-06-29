"""Extract plain text from meeting documents (pdf/txt/md/docx) via MarkItDown."""
import os

# Lazy init — avoids hanging at import time when MarkItDown loads optional deps
_converter = None


def _get_converter():
    global _converter
    if _converter is None:
        from markitdown import MarkItDown
        _converter = MarkItDown()
    return _converter


def extract(doc_path: str) -> str:
    """Return structured text content from a document file.

    Supports pdf, txt, md, docx. Preserves headings when present.
    Raises RuntimeError with a user-friendly message on failure.
    """
    if not os.path.exists(doc_path):
        raise FileNotFoundError(f"Document file not found: {doc_path}")

    ext = os.path.splitext(doc_path)[1].lstrip(".").lower()
    allowed = {"pdf", "txt", "md", "docx"}
    if ext not in allowed:
        raise ValueError(f"Unsupported document format '.{ext}'. Use: {', '.join(sorted(allowed))}.")

    try:
        result = _get_converter().convert(doc_path)
    except Exception as exc:
        raise RuntimeError(f"Failed to extract text from document: {exc}") from exc

    text = (result.text_content or "").strip()
    if not text:
        raise RuntimeError("Document appears to be empty or contains no extractable text.")
    return text
