"""
Fact Check Tools tests. They use a fake HTTP transport, so there is no internet
and no real key. REAL_RESPONSE copies the shape of a live Google reply.
"""

import asyncio

import httpx
import pytest

from models import Claim, ScanResult
from services import factcheck_service as fc

REAL_RESPONSE = {
    "claims": [
        {
            "text": "NASA has admitted the earth is flat in several documents.",
            "claimant": "Social media users",
            "claimReview": [
                {
                    "publisher": {"name": "AAP", "site": "aap.com.au"},
                    "url": "https://www.aap.com.au/factcheck/no-nasa-didnt-admit-the-earth-is-flat/",
                    "title": "No, NASA didn't admit the earth is flat",
                    "reviewDate": "2025-07-22T12:10:04Z",
                    "textualRating": "False. The post misinterprets common methodologies.",
                    "languageCode": "en",
                }
            ],
        },
        {
            "text": "Flights from New Zealand to Argentina connect through the U.S.",
            "claimant": "Viral social media post",
            "claimDate": "2025-02-14T00:00:00Z",
            "claimReview": [
                {
                    "publisher": {"name": "Science Feedback", "site": "science.feedback.org"},
                    "url": "https://science.feedback.org/review/flight-paths/",
                    "title": "Flight paths are not evidence for a flat Earth",
                    "reviewDate": "2025-02-26T00:00:00Z",
                    "textualRating": "Inaccurate",
                    "languageCode": "en",
                }
            ],
        },
    ]
}
KEY = "secret-test-key-123"


def scan(*texts) -> ScanResult:
    return ScanResult(
        claims=[Claim(text=t, verdict="false", reasoning="r") for t in texts]
    )


def run(result, handler):
    return asyncio.run(fc.enrich_scan_result(result, transport=httpx.MockTransport(handler)))


@pytest.fixture(autouse=True)
def with_key(monkeypatch):
    monkeypatch.setenv("GOOGLE_FACTCHECK_API_KEY", KEY)
    monkeypatch.delenv("GOOGLE_FACTCHECK_LANGUAGE_CODE", raising=False)


def test_parse_real_response_shape():
    items = fc._parse_fact_checks(REAL_RESPONSE)
    assert len(items) == 2
    assert items[0].publisher == "AAP"
    assert items[0].rating.startswith("False.")
    assert items[0].url.startswith("https://www.aap.com.au/")
    assert items[0].review_date == "2025-07-22T12:10:04Z"


def test_parse_empty_reply_is_not_an_error():
    assert fc._parse_fact_checks({}) == []


def test_parse_missing_optional_fields():
    payload = {"claims": [{"claimReview": [{"url": "https://x.example/a"}]}]}
    item = fc._parse_fact_checks(payload)[0]
    assert item.publisher == "Unknown publisher"
    assert item.rating == "No rating"
    assert item.review_date is None


def test_parse_keeps_at_most_three_per_claim():
    reviews = [{"url": f"https://x.example/{i}"} for i in range(6)]
    payload = {"claims": [{"claimReview": reviews}]}
    assert len(fc._parse_fact_checks(payload)) == fc.MAX_RESULTS_PER_CLAIM


def test_not_configured_without_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_FACTCHECK_API_KEY")

    def must_not_be_called(request):
        raise AssertionError("no HTTP call is allowed without a key")

    result = run(scan("a claim"), must_not_be_called)
    assert result.fact_check_status == "not_configured"
    assert result.claims[0].fact_checks == []


def test_match_found_sets_ok_and_attaches_evidence():
    result = run(scan("earth is flat"), lambda r: httpx.Response(200, json=REAL_RESPONSE))
    assert result.fact_check_status == "ok"
    assert result.claims[0].fact_checks[0].publisher == "AAP"
    assert result.claims[0].verdict == "false"  # the verdict is never changed


def test_no_match_is_ok_with_empty_list():
    result = run(scan("obscure claim"), lambda r: httpx.Response(200, json={}))
    assert result.fact_check_status == "ok"
    assert result.claims[0].fact_checks == []


def test_no_claims_means_no_lookup():
    def must_not_be_called(request):
        raise AssertionError("nothing to look up")

    result = run(scan(), must_not_be_called)
    assert result.fact_check_status == "ok"


def test_timeout_marks_unavailable_but_keeps_scan():
    def slow(request):
        raise httpx.ReadTimeout("too slow", request=request)

    result = run(scan("a claim"), slow)
    assert result.fact_check_status == "unavailable"
    assert result.claims[0].verdict == "false"
    assert result.claims[0].fact_checks == []


@pytest.mark.parametrize("status", [403, 429, 500])
def test_http_errors_mark_unavailable(status):
    result = run(scan("a claim"), lambda r: httpx.Response(status, json={"error": "x"}))
    assert result.fact_check_status == "unavailable"


def test_one_failed_claim_does_not_lose_the_others():
    def handler(request):
        if "bad" in request.url.params["query"]:
            return httpx.Response(500)
        return httpx.Response(200, json=REAL_RESPONSE)

    result = run(scan("good claim", "bad claim"), handler)
    assert result.fact_check_status == "unavailable"
    assert result.claims[0].fact_checks and not result.claims[1].fact_checks


def test_key_never_appears_in_error_text():
    async def go():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda r: httpx.Response(403))
        ) as client:
            await fc.lookup_fact_checks(client, "claim", KEY)

    with pytest.raises(fc.FactCheckLookupError) as info:
        asyncio.run(go())
    assert KEY not in str(info.value)


def test_language_code_is_sent_only_when_configured(monkeypatch):
    seen = []

    def handler(request):
        seen.append(dict(request.url.params))
        return httpx.Response(200, json={})

    run(scan("claim"), handler)
    assert "languageCode" not in seen[0]

    monkeypatch.setenv("GOOGLE_FACTCHECK_LANGUAGE_CODE", "id")
    run(scan("claim"), handler)
    assert seen[1]["languageCode"] == "id"