# MeetMind — Demo

Multimodal meeting notes system (CS117 — Nhóm 5, UIT).

**Pipeline:** audio + document → transcript (ElevenLabs Scribe) → analysis (DeepSeek) → PDF with summary, to-do list, and conflict warnings.

## Quick Start

```bash
# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up API keys
copy .env.example .env          # Windows
# cp .env.example .env          # macOS/Linux
# Edit .env and fill in your keys

# 4. Run
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## API Keys Required

| Key | Where to get |
|-----|-------------|
| `ELEVENLABS_API_KEY` | https://elevenlabs.io — free tier available |
| `DEEPSEEK_API_KEY` | https://platform.deepseek.com — free credits on signup |

## Input Constraints

| Type | Formats | Limit |
|------|---------|-------|
| Audio | `.mp3`, `.m4a`, `.wav` | ≤ 50 MB |
| Document | `.pdf`, `.docx`, `.md`, `.txt` | ≤ 50 MB |

**Demo tip:** Use a short audio clip (2–5 min) to save ElevenLabs STT credits.

## Output

A downloadable PDF containing:
- **Summary** — key meeting content
- **To-do list** — task · assignee · deadline · source quote
- **Conflict Warning** — discrepancies between audio and document (with verbatim quotes from both sources)

## Project Structure

```
meetmind/
├── app.py                    # Streamlit UI
├── requirements.txt
├── .env.example
├── src/
│   ├── config.py             # API keys + constants
│   ├── audio_transcription.py  # ElevenLabs Scribe STT
│   ├── slide_extraction.py   # MarkItDown document parser
│   ├── content_analysis.py   # DeepSeek JSON analysis
│   ├── output_generator.py   # HTML + PDF renderer
│   └── pipeline.py           # Orchestrator
├── prompts/
│   └── analysis_prompt.py    # System + user prompts
└── samples/                  # Put your test files here
```
