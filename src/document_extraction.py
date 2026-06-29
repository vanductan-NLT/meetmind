"""Extract plain text from meeting documents (pdf/txt/md/docx/json) via MarkItDown."""
import os
import json

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

    Supports pdf, txt, md, docx, json. Preserves headings when present.
    Raises RuntimeError with a user-friendly message on failure.
    """
    if not os.path.exists(doc_path):
        raise FileNotFoundError(f"Document file not found: {doc_path}")

    ext = os.path.splitext(doc_path)[1].lstrip(".").lower()
    allowed = {"pdf", "txt", "md", "docx", "json"}
    if ext not in allowed:
        raise ValueError(f"Unsupported document format '.{ext}'. Use: {', '.join(sorted(allowed))}.")

    # JSON: dump as readable text instead of going through MarkItDown
    if ext == "json":
        return _extract_json(doc_path)

    try:
        result = _get_converter().convert(doc_path)
    except Exception as exc:
        raise RuntimeError(f"Failed to extract text from document: {exc}") from exc

    text = (result.text_content or "").strip()
    if not text:
        raise RuntimeError("Document appears to be empty or contains no extractable text.")
    return text


def _extract_json(doc_path: str) -> str:
    """Read a JSON file and return it as indented text for the LLM."""
    try:
        with open(doc_path, encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps(data, ensure_ascii=False, indent=2)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON file: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to read JSON file: {exc}") from exc
