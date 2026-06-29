"""Load environment variables and shared constants.

Supports two sources for API keys (in priority order):
1. Streamlit Cloud secrets (st.secrets) — used when deployed on streamlit.io/cloud
2. Local .env file via python-dotenv — used when running locally
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _get_secret(key: str) -> str:
    """Read a secret from st.secrets (Streamlit Cloud) or env var (local)."""
    try:
        import streamlit as st
        return st.secrets.get(key, os.getenv(key, ""))
    except Exception:
        return os.getenv(key, "")


ELEVENLABS_API_KEY: str = _get_secret("ELEVENLABS_API_KEY")
DEEPSEEK_API_KEY: str = _get_secret("DEEPSEEK_API_KEY")

STT_MODEL = "scribe_v1"
LLM_MODEL = "deepseek-chat"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

MAX_FILE_MB = 50
ALLOWED_AUDIO_EXT = {"mp3", "m4a", "wav"}
ALLOWED_DOC_EXT = {"pdf", "txt", "md", "docx"}


def validate_keys() -> None:
    """Raise ValueError if any required API key is missing."""
    missing = []
    if not ELEVENLABS_API_KEY:
        missing.append("ELEVENLABS_API_KEY")
    if not DEEPSEEK_API_KEY:
        missing.append("DEEPSEEK_API_KEY")
    if missing:
        raise ValueError(
            f"Missing API key(s): {', '.join(missing)}. "
            "Local: copy .env.example to .env and fill in your keys. "
            "Streamlit Cloud: add keys in App Settings → Secrets."
        )
