"""
Pipeline tests: the glue between extraction, lookups and the judge.
Everything external is replaced by fakes, so no internet and no keys.
"""

import asyncio
import json

from models import Claim, Passage
from services import evidence_service, judge_service, pipeline


def run(coro):
    return asyncio.run(coro)


def claim(verdict, reasoning="r"):
    return Claim(text="c", verdict=verdict, reasoning=reasoning)


def llm(claims, judge_reply=None, summary="s"):
    async def complete(system, user, max_tokens):
        if system == judge_service.EXTRACT_SYSTEM_PROMPT:
            return json.dumps({"source_summary": summary, "claims": claims})
        return json.dumps(judge_reply or {"verdict": "unverifiable", "reasoning": "r", "evidence": []})
    return complete


# ----------------------------------------------------------------- overall note

def test_overall_note_counts_only_present_verdicts():
    note = pipeline._overall_note([claim("false"), claim("false"), claim("unverifiable")], 100, "ok")
    assert note == "Checked 3 claims against sources: 2 false, 1 unverifiable."


def test_overall_note_singular_and_empty():
    assert pipeline._overall_note([claim("true")], 10, "ok") == "Checked 1 claim against sources: 1 true."
    assert pipeline._overall_note([], 10, "ok") == "No checkable factual claims were found."


def test_overall_note_mentions_search_problems_and_truncation():
    note = pipeline._overall_note([claim("unverifiable")], 99999, "not_configured")
    assert "not set up" in note and "first 6,000 characters" in note
    assert "failed" in pipeline._overall_note([claim("unverifiable")], 10, "unavailable")


# -------------------------------------------------------- missing-source reasons

def test_missing_source_reasons():
    none = claim("unverifiable", judge_service.NO_SOURCES_REASONING)
    assert "not set up" in pipeline._explain_missing_sources(none, "not_configured", "ok").reasoning
    assert "Try again" in pipeline._explain_missing_sources(none, "ok", "unavailable").reasoning
    assert "Try again" in pipeline._explain_missing_sources(none, "unavailable", "ok").reasoning
    assert pipeline._explain_missing_sources(none, "ok", "ok").reasoning == judge_service.NO_SOURCES_REASONING


def test_other_reasoning_is_left_alone():
    done = claim("false", "Verified quotes from 2 sources contradict this claim.")
    assert pipeline._explain_missing_sources(done, "not_configured", "unavailable") is done


# --------------------------------------------------------------- full pipeline

def test_pipeline_end_to_end(monkeypatch):
    monkeypatch.delenv("GOOGLE_FACTCHECK_API_KEY", raising=False)
    monkeypatch.setenv("TAVILY_API_KEY", "k")
    page = Passage(url="https://a.example", title="A", text="The sky appears blue because of Rayleigh scattering.", retrieved_at="t")

    async def search(client, text, key):
        return [page]

    monkeypatch.setattr(evidence_service, "search_evidence", search)
    monkeypatch.setattr(
        judge_service,
        "_groq_complete",
        llm(
            ["The sky is blue because of scattering"],
            {"verdict": "true", "reasoning": "r",
             "evidence": [{"source": "S1", "quote": "because of Rayleigh scattering", "stance": "supports"}]},
            summary="About the sky",
        ),
    )
    result = run(pipeline.verify_content("The sky is blue because of scattering."))
    assert result.source_summary == "About the sky"
    assert result.claims[0].verdict == "true"
    assert result.claims[0].evidence[0].url == "https://a.example"
    assert result.evidence_status == "ok"
    assert result.fact_check_status == "not_configured"
    assert result.overall_note.startswith("Checked 1 claim against sources: 1 true.")


def test_pipeline_with_no_claims(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_FACTCHECK_API_KEY", raising=False)
    monkeypatch.setattr(judge_service, "_groq_complete", llm([]))
    result = run(pipeline.verify_content("I love Mondays!"))
    assert result.claims == []
    assert result.overall_note.startswith("No checkable factual claims were found.")


def test_pipeline_extraction_failure_propagates_as_runtime_error(monkeypatch):
    async def boom(system, user, max_tokens):
        raise judge_service.JudgeError("Groq API request failed: boom")

    monkeypatch.setattr(judge_service, "_groq_complete", boom)
    try:
        run(pipeline.verify_content("x"))
        assert False, "should have raised"
    except RuntimeError:
        pass