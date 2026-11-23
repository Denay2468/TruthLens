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
    rating: str = Field(..., description="Publisher's verdict on the underlying claim")
    url: str = Field(..., description="URL of the published fact-check")
    title: str = Field(..., description="Title of the published fact-check")
    review_date: Optional[str] = Field(
        None, description="Date the fact-check was published or reviewed (ISO 8601)"
    )


class Claim(BaseModel):
    """A single fact-checked claim extracted from source content."""
    text: str = Field(..., description="The claim as extracted/paraphrased from the source")
    verdict: ClaimVerdict
    reasoning: str = Field(..., description="Brief explanation of why the model reached this verdict")
    fact_checks: List[FactCheck] = Field(
        default_factory=list,
        description="Published fact-checks matching this claim; empty when none exist",
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
            "Overall status of the fact-check lookups performed on this scan. "
            '"not_configured" means GOOGLE_FACTCHECK_API_KEY is not set; '
            '"ok" means every lookup completed; "unavailable" means a lookup failed.'
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