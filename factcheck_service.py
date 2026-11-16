"""
Wrapper around the Google Fact Check Tools API — the second "eye" of TruthLens.

Setup:
  1. Enable the Fact Check Tools API and create an API key:
       https://console.cloud.google.com/apis/api/factchecktolltools.googleapis.com
  2. Put the key in your .env file as GOOGLE_FACTCHECK_API_KEY=*** (see .env.example).
  3. pip install httpx

How it works ("dual-API"):
  1. Groq (groq_service.fact_check_text) extracts the claims — max 6 — together
     with a verdict (true / misleading / false / unverifiable) and reasoning.
     Groq is always the source of the verdict.
  2. After that, for each claim this module queries the Google Fact Check Tools
     API to find any published fact-check that matches the claim text.
  3. The API results are attached to each claim under `fact_checks`. They only
     add evidence; they never change the verdict.

Top-level ScanResult.fact_check_status is one of:
  - "not_configured" — GOOGLE_FACTCHECK_API_KEY is not set. The app still works.
  - "ok"           — every lookup that could be attempted completed (found
                     matches, found nothing, or there were no claims to look up).
  - "unavailable"  — a lookup timed out, was rate-limited or errored. The scan
                     still succeeds with Groq's verdicts; the failed claim just
                     gets an empty fact_checks list.

The caller (backend/routers/scanner.py) does:
    result = groq_service.fact_check_text(text)      # Groq verdicts
    result = factcheck_service.enrich_scan_result(result)  # attach evidence
    return result
"""

import os
import urllib.parse

import httpx
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional

from models import Claim, FactCheck, ScanResult

# URL + path for the public Google Fact Check Tools "claims:search" endpoint.
FACT_CHECK_API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

# Language used when no explicit override is present.
DEFAULT_LANGUAGE_CODE = "en"
DEFAULT_TIMEOUT_SECONDS = 10.0


class FactCheckLookupError(Exception):
    """Raised when the Fact Check Tools API cannot complete a lookup.

    Covers missing key, timeout, HTTP error and network error. The caller must
    not treat this as a scan failure: the scan still succeeds with the Groq
    verdicts, and the failed claim simply gets an empty fact_checks list.
    """


def _build_search_url(claim_text: str, language_code: str, api_key: str) -> str:
    """Build the Fact Check Tools search URL from its query parameters."""
    params = {
        "query": claim_text,
        "languageCode": language_code,
        "key": api_key,
    }
    return f"{FACT_CHECK_API_URL}?{urllib.parse.urlencode(params)}"


def _call_api(url: str, *, timeout: float) -> dict:
    """Low-level HTTP GET that returns the parsed JSON body of the response."""
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


def lookup_fact_checks(claim_text: str, *, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> List[FactCheck]:
    """Look up published fact-checks that match one claim.

    Returns an empty list when the claim has no published fact-check (normal,
    not an error). Raises FactCheckLookupError on any API failure.
    """
    api_key = os.environ.get("GOOGLE_FACTCHECK_API_KEY")
    if not api_key:
        raise FactCheckLookupError("GOOGLE_FACTCHECK_API_KEY is not set in the environment")

    language_code = os.environ.get("GOOGLE_FACTCHECK_LANGUAGE_CODE", DEFAULT_LANGUAGE_CODE)
    url = _build_search_url(claim_text, language_code, api_key)

    try:
        payload = _call_api(url, timeout=timeout)
    except httpx.TimeoutException as exc:
        raise FactCheckLookupError(f"Fact-check lookup timed out: {exc}") from exc
    except httpx.HTTPStatusError as exc:
        raise FactCheckLookupError(
            f"Fact-check lookup returned HTTP {exc.response.status_code}: {exc}"
        ) from exc
    except httpx.RequestError as exc:
        raise FactCheckLookupError(f"Fact-check lookup request failed: {exc}") from exc

    api_claims = payload.get("claims", [])
    fact_checks: List[FactCheck] = []

    for item in api_claims:
        claim = item.get("claim", item) if isinstance(item, dict) else None
        if not isinstance(claim, dict):
            continue

        publisher = claim.get("publisher")
        if isinstance(publisher, dict):
            publisher = publisher.get("name", "")

        fact_checks.append(
            FactCheck(
                publisher=str(publisher or ""),
                rating=str(claim.get("rating", "No rating")),
                url=str(claim.get("url") or ""),
                title=str(claim.get("title") or ""),
                review_date=claim.get("review_date"),
            )
        )

    return fact_checks


def _mark_not_configured(scan_result: ScanResult) -> ScanResult:
    """Return a copy of scan_result whose fact_check_status is "not_configured"."""
    return scan_result.model_copy(
        update={
            "fact_check_status": "not_configured",
            "claims": [claim.model_copy(update={"fact_checks": []}) for claim in scan_result.claims],
        }
    )


def enrich_scan_result(scan_result: ScanResult) -> ScanResult:
    """Attach published fact-checks to every claim and set fact_check_status.

    The lookup is best-effort: a timeout, rate limit or HTTP error never turns
    into a scan failure. The scan still succeeds with Groq's verdicts; a claim
    that could not be looked up simply has an empty fact_checks list.
    """
    api_key = os.environ.get("GOOGLE_FACTCHECK_API_KEY")
    if not api_key:
        return _mark_not_configured(scan_result)

    enriched_claims: List[Claim] = []
    status = "ok"

    for claim in scan_result.claims:
        try:
            checks = lookup_fact_checks(claim.text)
        except FactCheckLookupError:
            status = "unavailable"
            checks = []
        enriched_claims.append(claim.model_copy(update={"fact_checks": checks}))

    return scan_result.model_copy(
        update={
            "fact_check_status": status,
            "claims": enriched_claims,
        }
    )
