"""Load environment variables and shared constants.

Local dev: reads from .env via python-dotenv.
Streamlit Cloud: keys are injected via st.secrets at runtime (not at import time).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Read from env at import time (safe for both local and Streamlit Cloud).
# On Streamlit Cloud, keys must also be set as environment variables in Secrets
# (Streamlit injects st.secrets entries as env vars automatically since v1.28).
ASSEMBLYAI_API_KEY: str = os.getenv("ASSEMBLYAI_API_KEY", "")
DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")

STT_MODEL = "scribe_v1"
LLM_MODEL = "deepseek-chat"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

MAX_AUDIO_MB = 100
MAX_DOC_MB = 50
ALLOWED_AUDIO_EXT = {"mp3", "m4a", "wav"}
ALLOWED_DOC_EXT = {"pdf", "txt", "md", "docx", "json"}


def reload_keys() -> None:
    """Re-read keys at runtime (called by app.py so st.secrets is available)."""
    global ASSEMBLYAI_API_KEY, DEEPSEEK_API_KEY
    try:
        import streamlit as st
        ASSEMBLYAI_API_KEY = st.secrets.get("ASSEMBLYAI_API_KEY", os.getenv("ASSEMBLYAI_API_KEY", ""))
        DEEPSEEK_API_KEY = st.secrets.get("DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY", ""))
    except Exception:
        pass  # already loaded from .env above


def validate_keys() -> None:
    """Re-read secrets then raise ValueError if any key is missing."""
    reload_keys()
    missing = []
    if not ASSEMBLYAI_API_KEY:
        missing.append("ASSEMBLYAI_API_KEY")
    if not DEEPSEEK_API_KEY:
        missing.append("DEEPSEEK_API_KEY")
    if missing:
        raise ValueError(
            f"Missing API key(s): {', '.join(missing)}. "
            "Local: copy .env.example to .env and fill in your keys. "
            "Streamlit Cloud: add keys in App Settings → Secrets."
        )
