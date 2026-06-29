"""Load environment variables and shared constants."""
import os
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")

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
            "Copy .env.example to .env and fill in your keys."
        )
