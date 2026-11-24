"""
The whole evidence-based pipeline, in one place:

    extract claims  ->  published fact-checks + web search (in parallel)
                    ->  evidence-only judge  ->  ScanResult

The routers call verify_content() and nothing else, so text, URL and media scans
all get the same treatment. Any LLM failure raises JudgeError (a RuntimeError,
which the routers already turn into HTTP 502). Failed lookups never fail a scan:
the claim simply ends up "unverifiable" with an honest explanation.
"""

import asyncio
from typing import List

from models import Claim, ScanResult
from services import evidence_service, factcheck_service, judge_service

_VERDICT_ORDER = ("true", "false", "misleading", "unverifiable")


def _explain_missing_sources(claim: Claim, evidence_status: str, fact_check_status: str) -> Claim:
    """A claim with no sources: say WHY, instead of the generic message."""
    if claim.reasoning != judge_service.NO_SOURCES_REASONING:
        return claim
    if "unavailable" in (evidence_status, fact_check_status):
        reason = "The evidence search was unavailable just now, so this claim could not be checked. Try again."
    elif evidence_status == "not_configured":
        reason = "Web evidence search is not set up on this server, so this claim cannot be verified."
    else:
        return claim
    return claim.model_copy(update={"reasoning": reason})


def _overall_note(claims: List[Claim], content_length: int, evidence_status: str) -> str:
    if not claims:
        note = "No checkable factual claims were found."
    else:
        counts = [f"{sum(c.verdict == v for c in claims)} {v}" for v in _VERDICT_ORDER]
        counts = [c for c in counts if not c.startswith("0 ")]
        noun = "claim" if len(claims) == 1 else "claims"
        note = f"Checked {len(claims)} {noun} against sources: {', '.join(counts)}."

    if evidence_status == "not_configured":
        note += " Web evidence search is not set up, so only published fact-checks were used."
    elif evidence_status == "unavailable":
        note += " Some evidence searches failed, so some claims may be under-checked."
    if content_length > judge_service.MAX_CONTENT_CHARS:
        note += f" Only the first {judge_service.MAX_CONTENT_CHARS:,} characters were analyzed."
    return note


async def verify_content(content: str) -> ScanResult:
    summary, claim_texts = await judge_service.extract_claims(content)
    draft = ScanResult(
        source_summary=summary,
        claims=[Claim(text=t, verdict="unverifiable", reasoning="") for t in claim_texts],
    )

    # Both lookups only need the claim text, so run them side by side.
    enriched, (passages, evidence_status) = await asyncio.gather(
        factcheck_service.enrich_scan_result(draft),
        evidence_service.retrieve_passages(draft.claims),
    )

    judged = await judge_service.judge_all(enriched.claims, passages)
    judged = [_explain_missing_sources(c, evidence_status, enriched.fact_check_status) for c in judged]

    return enriched.model_copy(
        update={
            "claims": judged,
            "evidence_status": evidence_status,
            "overall_note": _overall_note(judged, len(content), evidence_status),
        }
    )