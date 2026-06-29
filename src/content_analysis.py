"""Analyze meeting transcript + document via DeepSeek and return structured JSON."""
import json
from openai import OpenAI
from src.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, LLM_MODEL
from prompts.analysis_prompt import SYSTEM_PROMPT, build_user_prompt

_REQUIRED_KEYS = {"summary", "todos", "conflicts"}


def analyze(transcript: str, doc_text: str) -> dict:
    """Return {summary, todos, conflicts} dict from DeepSeek analysis.

    Retries once on malformed JSON. Raises RuntimeError on persistent failure.
    """
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    user_prompt = build_user_prompt(transcript, doc_text)

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
        except Exception as exc:
            raise RuntimeError(f"DeepSeek API error: {exc}") from exc

        raw = response.choices[0].message.content or ""
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            if attempt == 0:
                continue  # retry once
            raise RuntimeError(f"DeepSeek returned invalid JSON after retry:\n{raw[:300]}")

        missing = _REQUIRED_KEYS - result.keys()
        if missing:
            if attempt == 0:
                continue
            raise RuntimeError(f"DeepSeek JSON missing keys {missing}. Raw:\n{raw[:300]}")

        # Ensure lists are always lists
        result.setdefault("todos", [])
        result.setdefault("conflicts", [])
        return result

    raise RuntimeError("DeepSeek analysis failed after 2 attempts.")
