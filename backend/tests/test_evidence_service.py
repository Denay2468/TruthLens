"""
Evidence retrieval tests. They use a fake HTTP transport, so there is no
internet and no real key.
"""

import asyncio

import httpx

from models import Claim
from services import evidence_service as ev

KEY = "tvly-secret-test-key"

REPLY = {
    "results": [
        {"url": "https://who.example/covid", "title": "WHO: COVID-19", "content": "  Lemon water   does not cure COVID-19. "},
        {"url": "https://who.example/covid", "title": "duplicate url", "content": "should be dropped"},
        {"url": "https://news.example/a", "title": "Empty", "content": ""},
        {"url": "https://news.example/b", "title": "Long", "content": "x" * 5000},
    ]
}


def claims(*texts):
    return [Claim(text=t, verdict="unverifiable", reasoning="r") for t in texts]


def run(coro):
    return asyncio.run(coro)


def test_not_configured_without_key(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    passages, status = run(ev.retrieve_passages(claims("a", "b")))
    assert status == "not_configured"
    assert passages == [[], []]


def test_parses_cleans_and_dedupes(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", KEY)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == f"Bearer {KEY}"
        assert KEY not in str(request.url)  # key must never be in the address
        return httpx.Response(200, json=REPLY)

    passages, status = run(
        ev.retrieve_passages(claims("Lemon water cures COVID"), transport=httpx.MockTransport(handler))
    )
    assert status == "ok"
    got = passages[0]
    assert [p.url for p in got] == ["https://who.example/covid", "https://news.example/b"]
    assert got[0].text == "Lemon water does not cure COVID-19."   # whitespace collapsed
    assert len(got[1].text) == ev.MAX_PASSAGE_CHARS                # truncated
    assert got[0].retrieved_at.endswith("+00:00")


def test_failure_is_contained_and_leaks_no_key(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", KEY)

    def handler(request: httpx.Request) -> httpx.Response:
        if "bad claim" in request.content.decode():
            return httpx.Response(429)
        return httpx.Response(200, json=REPLY)

    passages, status = run(
        ev.retrieve_passages(claims("good claim", "bad claim"), transport=httpx.MockTransport(handler))
    )
    assert status == "unavailable"
    assert len(passages[0]) == 2 and passages[1] == []


def test_error_message_has_no_key(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", KEY)

    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(500))) as c:
            await ev.search_evidence(c, "x", KEY)

    try:
        run(go())
        assert False, "should have raised"
    except ev.EvidenceSearchError as e:
        assert KEY not in str(e) and "500" in str(e)


def test_no_claims_is_ok(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", KEY)
    assert run(ev.retrieve_passages([])) == ([], "ok")