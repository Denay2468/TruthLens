"""
Pydantic models shared across the Scanner endpoints.
Keep this file dependency-light — it should not import routers or services,
so it can be imported anywhere without circular-import issues.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, HttpUrl, Field


ClaimVerdict = Literal["true", "misleading", "false", "unverifiable"]


class FactCheck(BaseModel):
    """One published fact-check attached to a claim as supporting evidence."""
    publisher: str = Field(..., description="Name of the fact-check publisher")
    rating: str = Field(..., description="The publisher's own rating, as free text")
    url: str = Field(..., description="Link to the published fact-check")
    title: str = Field("", description="Title of the published fact-check")
    review_date: Optional[str] = Field(None, description="Review date (ISO 8601), if given")


class Claim(BaseModel):
    """A single fact-checked claim extracted from source content."""
    text: str = Field(..., description="The claim as extracted/paraphrased from the source")
    verdict: ClaimVerdict
    reasoning: str = Field(..., description="Brief explanation of why the model reached this verdict")
    fact_checks: List[FactCheck] = Field(
        default_factory=list,
        description="Published fact-checks related to this claim; empty when none were found",
    )


class ScanResult(BaseModel):
    """Common response shape returned by all three scanner endpoints."""
    source_summary: Optional[str] = Field(
        None, description="Short summary of what was analyzed (page title, filename, or input snippet)"
    )
    claims: List[Claim]
    fact_check_status: Literal["ok", "not_configured", "unavailable"] = Field(
        "not_configured",
        description=(
            '"not_configured": no GOOGLE_FACTCHECK_API_KEY; "ok": every lookup finished '
            '(matches or none); "unavailable": at least one lookup failed'
        ),
    )
    overall_note: Optional[str] = Field(
        None, description="Optional one-line takeaway shown above the claim list"
    )


# ---------- Request bodies ----------

class UrlScanRequest(BaseModel):
    url: HttpUrl


class TextScanRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)