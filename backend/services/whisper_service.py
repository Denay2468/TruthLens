"""
Transcription via Groq's hosted Whisper API — no local model, no torch, no
multi-GB download. Uses the same GROQ_API_KEY you already have for fact-checking.

Why we switched from local (self-hosted) Whisper:
  - openai-whisper pulls in torch, a 1GB+ dependency that's slow to install
    and slow to run inference on without a GPU (which Render's free tier
    doesn't have anyway).
  - Groq hosts Whisper large-v3 and it's covered by the same free tier as
    the fact-checking calls, so there's no new account or cost.

Setup:
  - Nothing extra beyond what fact-checking already needs — just GROQ_API_KEY
    in your .env file.
  - Still requires ffmpeg on your machine/host IF you want to pre-process
    files locally, but for the basic supported formats (mp3, mp4, wav, m4a)
    Groq's API accepts them directly, so ffmpeg is no longer a hard requirement
    for this endpoint.
"""

import os
from typing import Optional

from groq import Groq

MODEL_NAME = "whisper-large-v3-turbo"  # fast + accurate; swap to "whisper-large-v3" for max accuracy

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


class TranscriptionError(Exception):
    pass


def transcribe_file(file_bytes: bytes, filename: str) -> str:
    """
    Send the uploaded audio/video bytes to Groq's hosted Whisper endpoint
    and return the transcript text.
    """
    client = get_client()  # raises RuntimeError if GROQ_API_KEY is missing — let that propagate as-is

    try:
        transcription = client.audio.transcriptions.create(
            file=(filename, file_bytes),
            model=MODEL_NAME,
            response_format="text",
        )
    except Exception as e:
        raise TranscriptionError(f"Transcription failed: {e}") from e

    # response_format="text" returns a plain string; some SDK versions wrap it —
    # handle both just in case.
    text = transcription if isinstance(transcription, str) else getattr(transcription, "text", "")
    text = text.strip()

    if not text:
        raise TranscriptionError("No speech could be transcribed from this file.")

    return text
