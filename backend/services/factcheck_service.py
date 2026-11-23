"""
Wrapper around the Google Fact Check Tools API — the second "eye" of TruthLens.

Setup:
  1. Enable the Fact Check Tools API and create an API key:
       https://console.cloud.google.com/apis/api/factchecktools.googleapis.com
  2. Put the key in your .env file as GOOGLE_FACTCHECK_API_KEY=*** (see .env.example).
"""

import os
import urllib.parse
from typing import List

import httpx

from models import Claim, FactCheck, ScanResult

FACT_CHECK_API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
DEFAULT_LANGUAGE_CODE = "en"
DEFAULT_TIMEOUT_SECONDS = 10.0


class FactCheckLookupError(Exception):
    """Raised when the Fact Check Tools API cannot complete a lookup."""


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


def lookup_fact_checks(
    claim_text: str, *, timeout: float = DEFAULT_TIMEOUT_SECONDS
) -> List[FactCheck]:
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
        if not isinstance(item, dict):
            continue
        reviews = item.get("claimReview", [])
        if not isinstance(reviews, list):
            continue

        for review in reviews:
            if not isinstance(review, dict):
                continue

            publisher = review.get("publisher")
            if isinstance(publisher, dict):
                publisher = publisher.get("name", "")

            fact_checks.append(
                FactCheck(
                    publisher=str(publisher or ""),
                    rating=str(review.get("textualRating") or "No rating"),
                    url=str(review.get("url") or ""),
                    title=str(review.get("title") or ""),
                    review_date=review.get("reviewDate"),
                )
            )

    return fact_checks


def _mark_not_configured(scan_result: ScanResult) -> ScanResult:
    """Return a copy of scan_result whose fact_check_status is 'not_configured'."""
    return scan_result.model_copy(
        update={
            "fact_check_status": "not_configured",
            "claims": [claim.model_copy(update={"fact_checks": []}) for claim in scan_result.claims],
        }
    )


def enrich_scan_result(scan_result: ScanResult) -> ScanResult:
    """Attach published fact-checks to every claim and set fact_check_status.

    Best-effort: timeouts, rate limits, or HTTP errors never fail the scan.
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