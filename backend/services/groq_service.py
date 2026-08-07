"""
Wrapper around the Groq API for fact-checking text content.

Setup:
  1. Sign up at https://console.groq.com and create a free API key.
  2. Put it in your .env file as GROQ_API_KEY=... (see .env.example).
  3. pip install groq

We use llama3-8b-8192 by default — fast and within the generous free tier
(30 req/min, 14,400 req/day at time of writing). Swap MODEL_NAME if Groq
deprecates it; check https://console.groq.com/docs/models for current models.
"""

import json
import os
from typing import Optional

from groq import Groq
from models import ScanResult

MODEL_NAME = "openai/gpt-oss-20b"
# Groq deprecated the entire llama3-*/llama-3.1/llama-3.3 chat model family in 2026
# in favor of their gpt-oss models. openai/gpt-oss-20b is fast and covers the free
# tier well; swap to "openai/gpt-oss-120b" for higher-quality reasoning if you have
# headroom. Always check https://console.groq.com/docs/models for what's current.

_client: Optional[Groq] = None


def get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to your .env file — "
                "see .env.example for the expected variable name."
            )
        _client = Groq(api_key=api_key)
    return _client


FACT_CHECK_SYSTEM_PROMPT = """You are a media literacy expert and fact-checker.

Given a piece of content, extract the most important factual claims and evaluate each one.

Respond with ONLY valid JSON (no markdown fences, no commentary) matching this exact shape:
{
  "source_summary": "one short sentence describing what this content is about",
  "overall_note": "one short sentence takeaway for the reader",
  "claims": [
    {
      "text": "the claim, stated plainly",
      "verdict": "true" | "misleading" | "false" | "unverifiable",
      "reasoning": "one or two sentences explaining the verdict"
    }
  ]
}

Rules:
- Extract at most 6 of the most significant claims. Do not pad the list.
- Be concise. Each "reasoning" should be 1-2 sentences.
- Use "unverifiable" when the claim cannot be checked without primary sources you don't have access to
  (e.g. personal anecdotes, private data) — do not guess.
- If the content contains no checkable factual claims (e.g. it's pure opinion or a product description
  with no factual assertions), return an empty claims list and explain why in overall_note.
"""


def fact_check_text(content: str) -> ScanResult:
    """
    Send `content` to Groq for fact-checking and return a validated ScanResult.
    Raises RuntimeError on API failure or if the model doesn't return valid JSON.
    """
    client = get_client()

    # Guard against sending excessively long content — truncate and note it.
    max_chars = 6000
    truncated = len(content) > max_chars
    payload_text = content[:max_chars]

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": FACT_CHECK_SYSTEM_PROMPT},
                {"role": "user", "content": f"Content to analyze:\n\n{payload_text}"},
            ],
            temperature=0.2,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )
    except Exception as e:
        raise RuntimeError(f"Groq API request failed: {e}") from e

    raw = completion.choices[0].message.content

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Groq did not return valid JSON: {e}\nRaw response: {raw[:500]}") from e

    result = ScanResult.model_validate(parsed)

    if truncated and result.overall_note:
        result.overall_note += " (Note: content was truncated for analysis.)"

    return result
