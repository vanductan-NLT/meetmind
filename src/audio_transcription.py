"""Transcribe meeting audio to text using AssemblyAI."""
import os
from src.config import ASSEMBLYAI_API_KEY


def transcribe(audio_path: str) -> str:
    """Return transcript text from an audio file (mp3/m4a/wav).

    Uses AssemblyAI with automatic language detection.
    Raises RuntimeError with a user-friendly message on failure.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    try:
        import assemblyai as aai
    except ImportError:
        raise RuntimeError("assemblyai not installed. Run: pip install assemblyai")

    aai.settings.api_key = ASSEMBLYAI_API_KEY

    config = aai.TranscriptionConfig(language_detection=True)
    transcriber = aai.Transcriber(config=config)

    try:
        transcript = transcriber.transcribe(audio_path)
    except Exception as e:
        raise RuntimeError(f"AssemblyAI request failed: {e}")

    if transcript.status == aai.TranscriptStatus.error:
        raise RuntimeError(f"Transcription failed: {transcript.error}")

    text = transcript.text or ""
    if not text:
        raise RuntimeError("AssemblyAI returned an empty transcript. Check audio quality.")
    return text
