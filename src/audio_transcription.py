"""Transcribe meeting audio to text using ElevenLabs Scribe STT."""
import os
import requests
from src.config import ELEVENLABS_API_KEY, STT_MODEL


def transcribe(audio_path: str) -> str:
    """Return transcript text from an audio file (mp3/m4a/wav).

    Uses ElevenLabs Scribe v1 via REST API for maximum compatibility.
    Raises RuntimeError with a user-friendly message on failure.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    url = "https://api.elevenlabs.io/v1/speech-to-text"
    headers = {"xi-api-key": ELEVENLABS_API_KEY}

    with open(audio_path, "rb") as f:
        ext = os.path.splitext(audio_path)[1].lstrip(".").lower()
        mime = _mime_type(ext)
        files = {"file": (os.path.basename(audio_path), f, mime)}
        data = {"model_id": STT_MODEL}

        try:
            response = requests.post(url, headers=headers, files=files, data=data, timeout=300)
        except requests.exceptions.Timeout:
            raise RuntimeError("ElevenLabs STT request timed out. Try a shorter audio clip.")
        except requests.exceptions.ConnectionError:
            raise RuntimeError("Cannot reach ElevenLabs API. Check your internet connection.")

    if response.status_code == 401:
        raise RuntimeError("Invalid ElevenLabs API key. Check your ELEVENLABS_API_KEY in .env.")
    if response.status_code == 422:
        raise RuntimeError("ElevenLabs rejected the file. Ensure audio is mp3/m4a/wav and under 50 MB.")
    if not response.ok:
        raise RuntimeError(f"ElevenLabs STT error {response.status_code}: {response.text[:200]}")

    result = response.json()
    text = result.get("text", "")
    if not text:
        raise RuntimeError("ElevenLabs returned an empty transcript. Check audio quality.")
    return text


def _mime_type(ext: str) -> str:
    return {"mp3": "audio/mpeg", "m4a": "audio/mp4", "wav": "audio/wav"}.get(ext, "audio/mpeg")
