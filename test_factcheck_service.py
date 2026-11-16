"""
Offline unit tests for the Google Fact Check Tools integration.

They never contact the internet: the HTTP layer is replaced with a fake, so
they run offline and for free.

Run from the backend folder:   pytest tests/test_factcheck_service.py -v
"""

import httpx

import pytest

from models import Claim, ScanResult
from services import factcheck_service

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_payload(**overrides):
    """Build a Fact Check Tools API response body (matches the real API shape)."""
    payload = {
        "claims": [
            {
                "claim": {
                    "id": "https://factcheck.example.com/claim/123",
                    "publisher": {"name": "Reuters"},
                    "review_date": "2024-01-15",
                    "text": "Water boils at 100C at sea level.",
                    "url": "https://factcheck.example.com/claim/123",
                    "title": "Check: Water boils at 100C.",
                    "rating": "True",
                    "language": "en",
                    "author": "Jane Doe",
                    "image": "https://example.com/image.png",
                    "keywords": ["water", "boiling"],
                    "date_published": "2024-01-10",
                }
            }
        ],
        "totalResults": 1,
        "limit": 20,
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


# ---------------------------------------------------------------------------
# lookup_fact_checks
# ---------------------------------------------------------------------------


def test_lookup_returns_published_fact_checks(monkeypatch):
    monkeypatch.setenv("GOOGLE_FACTCHECK_API_KEY", "test-key")
    monkeypatch.setattr(factcheck_service, "_call_api", _fake_call_api)

    result = factcheck_service.lookup_fact_checks("Water boils at 100C.")

    assert len(result) == 1
    claim = result[0]
    assert claim.publisher == "Reuters"
    assert claim.rating == "True"
    assert claim.url == "https://factcheck.example.com/claim/123"
    assert claim.title == "Check: Water boils at 100C."
    assert claim.review_date == "2024-01-15"


def test_lookup_no_match(monkeypatch):
    monkeypatch.setenv("GOOGLE_FACTCHECK_API_KEY", "test-key")
    monkeypatch.setattr(
        factcheck_service, "_call_api", lambda url, **kwargs: _make_payload(claims=[])
    )

    result = factcheck_service.lookup_fact_checks("Nothing matches here.")

    assert result == []


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
    request = httpx.Request("GET", "https://factcheck.example.com/claim/123")
    response = httpx.Response(500, request=request, content=b"internal server error")
    error = httpx.HTTPStatusError(
        "internal server error", request=request, response=response
    )

    def _boom(url, **kwargs):
        raise error

    monkeypatch.setattr(factcheck_service, "_call_api", _boom)

    with pytest.raises(factcheck_service.FactCheckLookupError, match="500"):
        factcheck_service.lookup_fact_checks("Water boils at 100C.")


# ---------------------------------------------------------------------------
# enrich_scan_result
# ---------------------------------------------------------------------------


def test_enrich_scan_result_ok_when_lookup_succeeds(monkeypatch):
    monkeypatch.setenv("GOOGLE_FACTCHECK_API_KEY", "test-key")
    monkeypatch.setattr(factcheck_service, "_call_api", _fake_call_api)

    scan_result = _base_scan_result()
    enriched = factcheck_service.enrich_scan_result(scan_result)

    assert enriched.fact_check_status == "ok"
    assert enriched.source_summary == "A test content"
    assert enriched.overall_note == "A test note"
    assert len(enriched.claims) == 1
    claim = enriched.claims[0]
    assert len(claim.fact_checks) == 1
    fc = claim.fact_checks[0]
    assert fc.publisher == "Reuters"
    assert fc.rating == "True"
    assert fc.url == "https://factcheck.example.com/claim/123"
    assert fc.title == "Check: Water boils at 100C."
    assert fc.review_date == "2024-01-15"


def test_enrich_scan_result_ok_when_lookup_found_no_match(monkeypatch):
    monkeypatch.setenv("GOOGLE_FACTCHECK_API_KEY", "test-key")
    monkeypatch.setattr(
        factcheck_service, "_call_api", lambda url, **kwargs: _make_payload(claims=[])
    )

    scan_result = _base_scan_result()
    enriched = factcheck_service.enrich_scan_result(scan_result)

    assert enriched.fact_check_status == "ok"
    assert enriched.claims[0].fact_checks == []


def test_enrich_scan_result_unavailable_when_lookup_fails(monkeypatch):
    monkeypatch.setenv("GOOGLE_FACTCHECK_API_KEY", "test-key")

    def _boom(url, **kwargs):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(factcheck_service, "_call_api", _boom)

    scan_result = _base_scan_result()
    enriched = factcheck_service.enrich_scan_result(scan_result)

    assert enriched.fact_check_status == "unavailable"
    assert enriched.claims[0].fact_checks == []


def test_enrich_scan_result_not_configured_when_key_missing(monkeypatch):
    monkeypatch.delenv("GOOGLE_FACTCHECK_API_KEY", raising=False)

    scan_result = _base_scan_result()
    enriched = factcheck_service.enrich_scan_result(scan_result)

    assert enriched.fact_check_status == "not_configured"
    assert enriched.claims[0].fact_checks == []
