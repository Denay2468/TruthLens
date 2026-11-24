"""
Manual end-to-end check of Steps 1-3 with your REAL keys (not part of the app).

    python try_step3.py "Drinking hot water with lemon cures COVID-19."

Needs GROQ_API_KEY in .env. TAVILY_API_KEY and GOOGLE_FACTCHECK_API_KEY are
optional: without them the claim has no sources and stays "unverifiable".
"""

import asyncio
import sys

from dotenv import load_dotenv

load_dotenv()

from models import Claim, ScanResult  # noqa: E402
from services import evidence_service, factcheck_service, judge_service  # noqa: E402

DEFAULT_TEXT = (
    "Drinking hot water with lemon cures COVID-19. "
    "The Great Wall of China is visible from the Moon with the naked eye."
)


async def main(text: str) -> None:
    summary, texts = await judge_service.extract_claims(text)
    print(f"\nSUMMARY: {summary}")
    print(f"CLAIMS FOUND: {len(texts)}")

    claims = [Claim(text=t, verdict="unverifiable", reasoning="") for t in texts]
    scan = await factcheck_service.enrich_scan_result(ScanResult(claims=claims))
    claims = scan.claims
    passages, evidence_status = await evidence_service.retrieve_passages(claims)
    print(f"fact_check_status={scan.fact_check_status}  evidence_status={evidence_status}")

    for c, p in zip(claims, passages):
        print(f"\n- {c.text}\n    sources: {len(p)} web + {len(c.fact_checks)} fact-checks")

    judged = await judge_service.judge_all(claims, passages)
    for c in judged:
        print(f"\n=== {c.verdict.upper()}  {c.text}")
        print(f"    {c.reasoning}")
        for e in c.evidence:
            print(f"    [{e.stance}] \"{e.quote}\"\n        {e.url}")


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or DEFAULT_TEXT))