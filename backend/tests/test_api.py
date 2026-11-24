"""
Backend tests. They never call Groq or the internet: the AI service is
replaced with a fake, so they run offline and for free.

Run from the backend folder:   pytest
"""

import asyncio
import json

import pytest
from fastapi.testclient import TestClient

import ratelimit
from main import app
from models import Passage
from routers import scanner
from services import evidence_service, groq_service, judge_service, scraper, whisper_service

client = TestClient(app)


async def fake_llm(system, user, max_tokens):
    """Stands in for Groq: one claim when extracting, a 'true' verdict with a quote when judging."""
    if system == judge_service.EXTRACT_SYSTEM_PROMPT:
        return json.dumps({"source_summary": "A test summary", "claims": ["Water boils at 100C at sea level"]})
    return json.dumps({
        "verdict": "true",
        "reasoning": "r",
        "evidence": [{"source": "S1", "quote": "Water boils at 100 degrees Celsius at sea level", "stance": "supports"}],
    })


BOILING = Passage(
    url="https://physics.example/boiling",
    title="Boiling point",
    text="Water boils at 100 degrees Celsius at sea level.",
    retrieved_at="2026-11-24T00:00:00+00:00",
)


@pytest.fixture(autouse=True)
def reset_state(monkeypatch):
    ratelimit.reset()
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "20")
    monkeypatch.delenv("GOOGLE_FACTCHECK_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.setattr(judge_service, "_groq_complete", fake_llm)


# ---------- health ----------

def test_health():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---------- text ----------

def test_text_scan_without_evidence_keys_is_unverifiable_not_guessed():
    r = client.post("/api/scan/text", json={"text": "Water boils at 100C."})
    assert r.status_code == 200
    body = r.json()
    claim = body["claims"][0]
    assert claim["verdict"] == "unverifiable"      # no sources: the AI is not allowed to guess
    assert claim["evidence"] == []
    assert "not set up" in claim["reasoning"]
    assert body["evidence_status"] == "not_configured"


def test_text_scan_with_sources_gives_verdict_and_verified_quote(monkeypatch):
    async def fake_search(client, text, key):
        return [BOILING]

    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    monkeypatch.setattr(evidence_service, "search_evidence", fake_search)
    body = client.post("/api/scan/text", json={"text": "Water boils at 100C."}).json()
    claim = body["claims"][0]
    assert claim["verdict"] == "true"
    assert claim["evidence"][0]["url"] == BOILING.url
    assert claim["evidence"][0]["stance"] == "supports"
    assert body["evidence_status"] == "ok"
    assert body["overall_note"].startswith("Checked 1 claim against sources: 1 true.")


def test_failed_evidence_search_does_not_fail_the_scan(monkeypatch):
    async def broken_search(client, text, key):
        raise evidence_service.EvidenceSearchError("Evidence search timed out")

    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    monkeypatch.setattr(evidence_service, "search_evidence", broken_search)
    r = client.post("/api/scan/text", json={"text": "Water boils at 100C."})
    assert r.status_code == 200
    body = r.json()
    assert body["evidence_status"] == "unavailable"
    assert body["claims"][0]["verdict"] == "unverifiable"
    assert "Try again" in body["claims"][0]["reasoning"]


def test_text_scan_rejects_empty():
    assert client.post("/api/scan/text", json={"text": ""}).status_code == 422


def test_text_scan_rejects_too_long():
    assert client.post("/api/scan/text", json={"text": "x" * 8001}).status_code == 422


def test_text_scan_ai_failure_returns_502(monkeypatch):
    async def boom(system, user, max_tokens):
        raise judge_service.JudgeError("Groq API request failed: boom")
    monkeypatch.setattr(judge_service, "_groq_complete", boom)
    r = client.post("/api/scan/text", json={"text": "hello"})
    assert r.status_code == 502


# ---------- url ----------

def test_url_scan_ok(monkeypatch):
    async def fake_scrape(url):
        return {"title": "Page title", "text": "Some page text."}
    monkeypatch.setattr(scraper, "scrape_url", fake_scrape)
    r = client.post("/api/scan/url", json={"url": "https://example.com/a"})
    assert r.status_code == 200


def test_url_scan_invalid_url():
    assert client.post("/api/scan/url", json={"url": "not-a-url"}).status_code == 422


def test_url_scan_scrape_error_returns_422(monkeypatch):
    async def bad_scrape(url):
        raise scraper.ScrapeError("The page took too long to respond.")
    monkeypatch.setattr(scraper, "scrape_url", bad_scrape)
    r = client.post("/api/scan/url", json={"url": "https://example.com"})
    assert r.status_code == 422


@pytest.mark.parametrize("url", [
    "http://127.0.0.1/",
    "http://localhost:8000/",
    "http://169.254.169.254/latest/meta-data/",
    "http://10.0.0.5/",
    "http://[::1]/",
    "ftp://example.com/file",
])
def test_scraper_blocks_non_public_addresses(url):
    with pytest.raises(scraper.ScrapeError):
        asyncio.run(scraper.scrape_url(url))


# ---------- media ----------

def test_media_rejects_bad_extension():
    r = client.post("/api/scan/media", files={"file": ("virus.exe", b"abc", "application/octet-stream")})
    assert r.status_code == 415


def test_media_rejects_empty_file():
    r = client.post("/api/scan/media", files={"file": ("a.mp3", b"", "audio/mpeg")})
    assert r.status_code == 400


def test_media_rejects_oversized_file(monkeypatch):
    monkeypatch.setattr(scanner, "MAX_UPLOAD_BYTES", 1024)
    r = client.post("/api/scan/media", files={"file": ("a.mp3", b"x" * 2048, "audio/mpeg")})
    assert r.status_code == 413


def test_media_ok(monkeypatch):
    monkeypatch.setattr(whisper_service, "transcribe_file", lambda b, name: "a transcript")
    r = client.post("/api/scan/media", files={"file": ("a.mp3", b"abc", "audio/mpeg")})
    assert r.status_code == 200
    assert r.json()["claims"]


def test_media_transcription_failure_returns_422(monkeypatch):
    def fail(b, name):
        raise whisper_service.TranscriptionError("No speech could be transcribed from this file.")
    monkeypatch.setattr(whisper_service, "transcribe_file", fail)
    r = client.post("/api/scan/media", files={"file": ("a.mp3", b"abc", "audio/mpeg")})
    assert r.status_code == 422


# ---------- rate limit / CORS / model output ----------

def test_rate_limit_returns_429(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "3")
    codes = [client.post("/api/scan/text", json={"text": "hi"}).status_code for _ in range(5)]
    assert codes[:3] == [200, 200, 200]
    assert codes[3] == 429


def test_cors_allows_local_dev_origin_only():
    ok = client.get("/", headers={"Origin": "http://localhost:5173"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    other = client.get("/", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in other.headers


def test_bad_model_json_shape_becomes_runtime_error(monkeypatch):
    class Msg:  # minimal stand-in for the Groq response object
        content = '{"claims": [{"text": "x", "verdict": "banana", "reasoning": "r"}]}'
    class Choice:
        message = Msg()
    class Completion:
        choices = [Choice()]
    class FakeClient:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    return Completion()
    monkeypatch.undo()  # use the real fact_check_text for this test
    monkeypatch.setattr(groq_service, "get_client", lambda: FakeClient())
    with pytest.raises(RuntimeError):
        groq_service.fact_check_text("hello")


# ---------- scraper success path (local test page, no internet) ----------

def test_scraper_extracts_article_text(monkeypatch):
    import http.server
    import threading

    html = b"<html><head><title>Test Page</title></head><body><nav>menu</nav><article><p>Hello claim world.</p></article></body></html>"

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html)
        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        # The safety check blocks 127.0.0.1 by design, so switch it off for this one test.
        monkeypatch.setattr(scraper, "_check_public_url_sync", lambda url: None)
        result = asyncio.run(scraper.scrape_url(f"http://127.0.0.1:{server.server_port}/"))
    finally:
        server.shutdown()

    assert result["title"] == "Test Page"
    assert "Hello claim world." in result["text"]
    assert "menu" not in result["text"]
    
# ---------- fact-check evidence reaches the API response ----------

def test_scan_response_includes_fact_check_fields(monkeypatch):
    r = client.post("/api/scan/text", json={"text": "Water boils at 100C."})
    body = r.json()
    assert body["fact_check_status"] == "not_configured"
    assert body["claims"][0]["fact_checks"] == []


def test_scan_response_carries_evidence_when_key_is_set(monkeypatch):
    from models import FactCheck
    from services import factcheck_service

    async def fake_lookup(client, text, key):
        return [FactCheck(publisher="AAP", rating="False", url="https://x.example/a", title="t")]

    monkeypatch.setenv("GOOGLE_FACTCHECK_API_KEY", "test-key")
    monkeypatch.setattr(factcheck_service, "lookup_fact_checks", fake_lookup)
    body = client.post("/api/scan/text", json={"text": "Water boils at 100C."}).json()
    assert body["fact_check_status"] == "ok"
    assert body["claims"][0]["fact_checks"][0]["publisher"] == "AAP"