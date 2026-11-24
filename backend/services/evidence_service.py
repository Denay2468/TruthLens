"""
Web evidence retrieval (Step 2 of the evidence-based pipeline).

For each claim we search the web and keep the returned text passages. Nothing
here decides a verdict: the judge (Step 3) reads these passages and may only
use what they actually say.

Provider: Tavily (https://tavily.com), a search API built for LLM pipelines.
Check their site for current free-tier limits.

Status (same idea as fact_check_status):
  "not_configured"  TAVILY_API_KEY is not set. The app still works.
  "ok"              every search finished (results or none: both are normal).
  "unavailable"     at least one search timed out, was rate limited or failed.

Environment:
  TAVILY_API_KEY   required to turn evidence retrieval on

Security: the key is sent in a header, and error messages never include it.
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import List, Optional, Tuple

import httpx

from models import Claim, Passage

TAVILY_URL = "https://api.tavily.com/search"
TIMEOUT_SECONDS = 10.0
MAX_RESULTS_PER_CLAIM = 5
MAX_PASSAGE_CHARS = 1500
MAX_QUERY_CHARS = 400


class EvidenceSearchError(Exception):
    """A search could not finish. Never contains the key."""


def _parse_results(payload: dict, retrieved_at: str) -> List[Passage]:
    """Turn a Tavily reply into Passages: skip empty text, keep one per URL."""
    passages: List[Passage] = []
    seen = set()
    for item in payload.get("results", []) or []:
        url = (item.get("url") or "").strip()
        text = " ".join((item.get("content") or "").split())
        if not url or not text or url in seen:
            continue
        seen.add(url)
        passages.append(
            Passage(
                url=url,
                title=(item.get("title") or "").strip(),
                text=text[:MAX_PASSAGE_CHARS],
                retrieved_at=retrieved_at,
            )
        )
    return passages[:MAX_RESULTS_PER_CLAIM]


async def search_evidence(
    client: httpx.AsyncClient, claim_text: str, api_key: str
) -> List[Passage]:
    """Search for one claim. Raises EvidenceSearchError on any failure."""
    body = {
        "query": claim_text[:MAX_QUERY_CHARS],
        "search_depth": "basic",
        "max_results": MAX_RESULTS_PER_CLAIM,
        "include_answer": False,  # we never want a ready-made AI answer here
    }
    try:
        response = await client.post(
            TAVILY_URL, json=body, headers={"Authorization": f"Bearer {api_key}"}
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.TimeoutException:
        raise EvidenceSearchError("Evidence search timed out") from None
    except httpx.HTTPStatusError as exc:
        raise EvidenceSearchError(f"Evidence search returned HTTP {exc.response.status_code}") from None
    except (httpx.RequestError, ValueError):
        raise EvidenceSearchError("Evidence search failed") from None

    return _parse_results(payload, datetime.now(timezone.utc).isoformat(timespec="seconds"))


async def retrieve_passages(
    claims: List[Claim], *, transport: Optional[httpx.AsyncBaseTransport] = None
) -> Tuple[List[List[Passage]], str]:
    """
    Search the web for every claim, in parallel.
    Returns (passages, status): `passages[i]` belongs to `claims[i]`.
    Best effort: a failed search leaves that claim with no passages and sets
    status "unavailable"; it never fails the scan.
    `transport` is only for tests (a fake HTTP transport).
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return [[] for _ in claims], "not_configured"
    if not claims:
        return [], "ok"

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS, transport=transport) as client:
        outcomes = await asyncio.gather(
            *(search_evidence(client, c.text, api_key) for c in claims),
            return_exceptions=True,
        )

    status = "ok"
    passages: List[List[Passage]] = []
    for outcome in outcomes:
        if isinstance(outcome, EvidenceSearchError):
            status = "unavailable"
            passages.append([])
        elif isinstance(outcome, BaseException):
            raise outcome  # a real bug: do not hide it
        else:
            passages.append(outcome)
    return passages, status