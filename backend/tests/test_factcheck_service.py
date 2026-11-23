"""
Offline unit tests for the Google Fact Check Tools integration.
Run from the backend folder:   pytest tests/test_factcheck_service.py -v
"""

import httpx
import pytest

from models import Claim, ScanResult
from services import factcheck_service


def _make_payload(**overrides):
    """Build a Google Fact Check Tools API response body (v1alpha1/claims:search)."""
    payload = {
        "claims": [
            {
                "text": "Water boils at 100C at sea level.",
                "claimant": "Example source",
                "claimReview": [
                    {
                        "publisher": {"name": "Reuters", "site": "reuters.com"},
                        "url": "https://factcheck.example.com/claim/123",
                        "title": "Check: Water boils at 100C.",
                        "reviewDate": "2024-01-15T00:00:00Z",
                        "textualRating": "True",
                        "languageCode": "en",
                    }
                ],
            }
        ]
    }
    payload.update(overrides)
    return payload


def _fake_call_api(url, **kwargs):
    return _make_payload()


def _base_scan_result():
    return ScanResult(
        source_summary="A test content",
        overall_note="A test note",
        claims=[
            Claim(
                text="Water boils at 100C at sea level.",
                verdict="true",
                reasoning="Basics of physics.",
            )
        ],
    )


def test_lookup_returns_published_fact_checks(monkeypatch):
    monkeypatch.setenv("GOOGLE_FACTCHECK_API_KEY", "test-key")
    monkeypatch.setattr(factcheck_service, "_call_api", _fake_call_api)

    result = factcheck_service.lookup_fact_checks("Water boils at 100C.")

    assert len(result) == 1
    fc = result[0]
    assert fc.publisher == "Reuters"
    assert fc.rating == "True"
    assert fc.url == "https://factcheck.example.com/claim/123"
    assert fc.title == "Check: Water boils at 100C."
    assert fc.review_date == "2024-01-15T00:00:00Z"


def test_lookup_no_match(monkeypatch):
    monkeypatch.setenv("GOOGLE_FACTCHECK_API_KEY", "test-key")
    monkeypatch.setattr(
        factcheck_service, "_call_api", lambda url, **kwargs: _make_payload(claims=[])
    )

    assert factcheck_service.lookup_fact_checks("Nothing matches here.") == []


def test_lookup_missing_key_raises(monkeypatch):
    monkeypatch.delenv("GOOGLE_FACTCHECK_API_KEY", raising=False)

    with pytest.raises(factcheck_service.FactCheckLookupError, match="not set"):
        factcheck_service.lookup_fact_checks("Water boils at 100C.")


def test_lookup_timeout_raises(monkeypatch):
    monkeypatch.setenv("GOOGLE_FACTCHECK_API_KEY", "test-key")

    def _boom(url, **kwargs):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(factcheck_service, "_call_api", _boom)

    with pytest.raises(factcheck_service.FactCheckLookupError, match="timed out"):
        factcheck_service.lookup_fact_checks("Water boils at 100C.")


def test_lookup_http_error_raises(monkeypatch):
    monkeypatch.setenv("GOOGLE_FACTCHECK_API_KEY", "test-key")
    request = httpx.Request("GET", "https://factchecktools.googleapis.com/v1alpha1/claims:search")
    response = httpx.Response(500, request=request, content=b"internal server error")
    error = httpx.HTTPStatusError("internal server error", request=request, response=response)

    def _boom(url, **kwargs):
        raise error

    monkeypatch.setattr(factcheck_service, "_call_api", _boom)

    with pytest.raises(factcheck_service.FactCheckLookupError, match="500"):
        factcheck_service.lookup_fact_checks("Water boils at 100C.")


def test_enrich_scan_result_ok_when_lookup_succeeds(monkeypatch):
    monkeypatch.setenv("GOOGLE_FACTCHECK_API_KEY", "test-key")
    monkeypatch.setattr(factcheck_service, "_call_api", _fake_call_api)

    enriched = factcheck_service.enrich_scan_result(_base_scan_result())

    assert enriched.fact_check_status == "ok"
    assert enriched.claims[0].fact_checks[0].publisher == "Reuters"
    assert enriched.claims[0].fact_checks[0].rating == "True"


def test_enrich_scan_result_ok_when_lookup_found_no_match(monkeypatch):
    monkeypatch.setenv("GOOGLE_FACTCHECK_API_KEY", "test-key")
    monkeypatch.setattr(
        factcheck_service, "_call_api", lambda url, **kwargs: _make_payload(claims=[])
    )

    enriched = factcheck_service.enrich_scan_result(_base_scan_result())

    assert enriched.fact_check_status == "ok"
    assert enriched.claims[0].fact_checks == []


def test_enrich_scan_result_unavailable_when_lookup_fails(monkeypatch):
    monkeypatch.setenv("GOOGLE_FACTCHECK_API_KEY", "test-key")

    def _boom(url, **kwargs):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(factcheck_service, "_call_api", _boom)

    enriched = factcheck_service.enrich_scan_result(_base_scan_result())

    assert enriched.fact_check_status == "unavailable"
    assert enriched.claims[0].fact_checks == []


def test_enrich_scan_result_not_configured_when_key_missing(monkeypatch):
    monkeypatch.delenv("GOOGLE_FACTCHECK_API_KEY", raising=False)

    enriched = factcheck_service.enrich_scan_result(_base_scan_result())

    assert enriched.fact_check_status == "not_configured"
    assert enriched.claims[0].fact_checks == []