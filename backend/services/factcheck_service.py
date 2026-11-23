"""
Google Fact Check Tools API: adds published fact-checks as evidence.

Flow: Groq extracts the claims and gives the verdicts (always the source of the
verdict). This module then looks up each claim and attaches any related
published fact-checks. The evidence never changes the verdict.

ScanResult.fact_check_status:
  "not_configured"  GOOGLE_FACTCHECK_API_KEY is not set. The app still works.
  "ok"              every lookup finished (matches found, or none: both are normal).
  "unavailable"     at least one lookup timed out, was rate limited or failed.
                    The scan still succeeds with the Groq verdicts.

Environment:
  GOOGLE_FACTCHECK_API_KEY            required to turn the lookup on
  GOOGLE_FACTCHECK_LANGUAGE_CODE      optional, for example "en"; unset = all languages

Security: the key travels in the request address, so error messages here never
include the address. Do not turn on INFO logging for httpx in production.
"""

import asyncio
import os
from typing import List, Optional

import httpx

from models import Claim, FactCheck, ScanResult

FACT_CHECK_API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
TIMEOUT_SECONDS = 5.0
MAX_RESULTS_PER_CLAIM = 3
MAX_QUERY_CHARS = 500


class FactCheckLookupError(Exception):
    """A lookup could not finish. Never contains the request address or the key."""


def _parse_fact_checks(payload: dict) -> List[FactCheck]:
    """
    Turn a claims:search response into FactCheck items.

    Real response shape (verified with a live request):
      { "claims": [ { "text", "claimant", "claimDate"?,
                      "claimReview": [ { "publisher": {"name","site"}, "url",
                                         "title", "reviewDate"?, "textualRating",
                                         "languageCode" } ] } ] }
    An empty reply ({}) means no published fact-check was found.
    """
    found: List[FactCheck] = []
    for item in payload.get("claims", []) or []:
        for review in (item.get("claimReview") or []):
            url = review.get("url")
            if not url:
                continue
            publisher = review.get("publisher") or {}
            found.append(
                FactCheck(
                    publisher=publisher.get("name") or publisher.get("site") or "Unknown publisher",
                    rating=review.get("textualRating") or "No rating",
                    url=url,
                    title=review.get("title") or "",
                    review_date=review.get("reviewDate"),
                )
            )
            if len(found) >= MAX_RESULTS_PER_CLAIM:
                return found
    return found


async def lookup_fact_checks(
    client: httpx.AsyncClient, claim_text: str, api_key: str
) -> List[FactCheck]:
    """Look up one claim. Raises FactCheckLookupError on any failure."""
    params = {"query": claim_text[:MAX_QUERY_CHARS], "key": api_key}
    language = os.environ.get("GOOGLE_FACTCHECK_LANGUAGE_CODE")
    if language:
        params["languageCode"] = language

    try:
        response = await client.get(FACT_CHECK_API_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    except httpx.TimeoutException:
        raise FactCheckLookupError("Fact-check lookup timed out") from None
    except httpx.HTTPStatusError as exc:
        # Status code only: str(exc) would contain the address and the key.
        raise FactCheckLookupError(f"Fact-check lookup returned HTTP {exc.response.status_code}") from None
    except (httpx.RequestError, ValueError):
        raise FactCheckLookupError("Fact-check lookup failed") from None

    return _parse_fact_checks(payload)


async def enrich_scan_result(
    scan_result: ScanResult, *, transport: Optional[httpx.AsyncBaseTransport] = None
) -> ScanResult:
    """
    Attach published fact-checks to every claim and set fact_check_status.
    Best effort: a failed lookup never fails the scan.
    `transport` is only for tests (a fake HTTP transport).
    """
    api_key = os.environ.get("GOOGLE_FACTCHECK_API_KEY")
    if not api_key:
        return scan_result.model_copy(update={"fact_check_status": "not_configured"})

    if not scan_result.claims:
        return scan_result.model_copy(update={"fact_check_status": "ok"})

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS, transport=transport) as client:
        outcomes = await asyncio.gather(
            *(lookup_fact_checks(client, claim.text, api_key) for claim in scan_result.claims),
            return_exceptions=True,
        )

    status = "ok"
    claims: List[Claim] = []
    for claim, outcome in zip(scan_result.claims, outcomes):
        if isinstance(outcome, FactCheckLookupError):
            status = "unavailable"
            claims.append(claim.model_copy(update={"fact_checks": []}))
        elif isinstance(outcome, BaseException):
            raise outcome  # a real bug: do not hide it
        else:
            claims.append(claim.model_copy(update={"fact_checks": outcome}))

    return scan_result.model_copy(update={"claims": claims, "fact_check_status": status})