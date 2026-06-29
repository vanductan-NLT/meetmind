# MeetMind — Demo

Multimodal meeting notes system (CS117 — Nhóm 5, UIT).

**Pipeline:** audio + document → transcript (AssemblyAI) → analysis (DeepSeek) → PDF with summary, to-do list, and conflict warnings.

## Quick Start

**PowerShell (recommended on Windows):**
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env        # then edit .env and fill in your keys
streamlit run app.py
```

**Git Bash on Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env          # then edit .env and fill in your keys
streamlit run app.py
```

> **Important:** Always activate the venv first. Running `streamlit` without activating
> uses the system Python and may fail with import errors.

Then open http://localhost:8501 in your browser.

## API Keys Required

| Key | Where to get |
|-----|-------------|
| `ASSEMBLYAI_API_KEY` | https://assemblyai.com — 5h free/month, no credit card |
| `DEEPSEEK_API_KEY` | https://platform.deepseek.com — free credits on signup |

## Input Constraints

| Type | Formats | Limit |
|------|---------|-------|
| Audio | `.mp3`, `.m4a`, `.wav` | ≤ 50 MB |
| Document | `.pdf`, `.docx`, `.md`, `.txt`, `.json` | ≤ 50 MB |

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
│   ├── audio_transcription.py  # AssemblyAI STT
│   ├── document_extraction.py  # MarkItDown document parser (pdf/docx/md/txt/json)
│   ├── content_analysis.py   # DeepSeek JSON analysis
│   ├── output_generator.py   # HTML + PDF renderer
│   └── pipeline.py           # Orchestrator
├── prompts/
│   └── analysis_prompt.py    # System + user prompts
└── samples/                  # Put your test files here
```
