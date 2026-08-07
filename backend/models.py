"""
Pydantic models shared across the Scanner endpoints.
Keep this file dependency-light — it should not import routers or services,
so it can be imported anywhere without circular-import issues.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, HttpUrl, Field


ClaimVerdict = Literal["true", "misleading", "false", "unverifiable"]


class Claim(BaseModel):
    """A single fact-checked claim extracted from source content."""
    text: str = Field(..., description="The claim as extracted/paraphrased from the source")
    verdict: ClaimVerdict
    reasoning: str = Field(..., description="Brief explanation of why the model reached this verdict")


class ScanResult(BaseModel):
    """Common response shape returned by all three scanner endpoints."""
    source_summary: Optional[str] = Field(
        None, description="Short summary of what was analyzed (page title, filename, or input snippet)"
    )
    claims: List[Claim]
    overall_note: Optional[str] = Field(
        None, description="Optional one-line takeaway shown above the claim list"
    )


# ---------- Request bodies ----------

class UrlScanRequest(BaseModel):
    url: HttpUrl


class TextScanRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)
