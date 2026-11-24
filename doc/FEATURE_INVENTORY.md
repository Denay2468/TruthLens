# TruthLens: Feature Inventory and Gap Analysis

**Task:** TL-1 Audit repository and alignment with the brief · **Status:** v1.0, updated for Sprint 3 (first audit: Sprint 1)
**Sources compared:** repository code, README and `doc/` files, the Group 4 presentation.
**Reviewer (another member):** _pending, add name and date_

## 1. Feature inventory (what the code does)

| # | Feature | Where in code | Status | Gap or note |
|---|---|---|---|---|
| 1 | Text scan | `routers/scanner.py` `scan_text` → `services/pipeline.py` | Working | Max 8000 characters in; at most 5 claims checked |
| 2 | URL scan | `scan_url`; `services/scraper.py` | Working | Static HTML only; private addresses blocked; **sites that block bots return HTTP 403** (fallback planned) |
| 3 | Media scan | `scan_media`; `services/whisper_service.py` | Working | **Speech only** (Whisper transcript), up to 25MB. Images and video frames are not analyzed |
| 4 | Claim extraction | `judge_service.extract_claims` | Working | The LLM lists checkable claims and gives no verdicts |
| 5 | Published fact-check lookup | `services/factcheck_service.py` | Working | Google Fact Check Tools API; optional key |
| 6 | Web evidence search | `services/evidence_service.py` | Working | Tavily; optional key; without it claims are `unverifiable` |
| 7 | Evidence-only judge | `judge_service.judge_claim` | Working | The model may only quote the numbered sources it is given |
| 8 | Quote validation and verdict rules | `judge_service.validate_evidence`, `decide_verdict` | Working | A quote must appear word for word in its source; verdict is capped by verified quotes |
| 9 | Claim-level verdicts | `models.py` `Claim` | Working | `true / misleading / false / unverifiable`; no numeric score (decision D3) |
| 10 | Explanation per claim | `judge_service.build_reasoning`, `pipeline._overall_note` | Working | Written by code from the verified quotes; the model's free text is never shown |
| 11 | Sources in results | `Claim.evidence[]` | **Working** | Verified quotes with stance, link and retrieval time. Closes the Sprint 1 gap |
| 12 | Scanner UI | `frontend/src` | Working | Tabs, verdict stamps, evidence cards with source links, notices when searches are off or failed. Demo "Test UI" buttons appear in dev mode only |
| 13 | "Not proof" disclaimer | `ScanResults.jsx` | Working | Reworded: verdicts rest on the quoted sources; users should open the links |
| 14 | Rate limiting | `ratelimit.py` | Working | In memory, per process; needs `--proxy-headers` behind Render |
| 15 | Caching | none | Missing | Planned |
| 16 | API keys kept server-side | `.env`, `.gitignore`, Render environment | Working | Groq, Tavily and Google keys; the Tavily key is sent in a header and never appears in error messages |
| 17 | Logo | `frontend/public/favicon.svg` | Partial | Confirm the status of the full logo with UI/UX |
| 18 | Responsiveness / accessibility | Tailwind, single column | Untested | TL-10: record the result |
| 19 | Deployment | Render (backend), Vercel (frontend) | **Done** | Live at <https://truthlens-blush-seven.vercel.app> |
| 20 | Automated tests | `backend/tests/` | Working | 84 offline tests when last run |
| 21 | Image / video manipulation detection | none | **Not started** | Planned: metadata, C2PA Content Credentials, reverse image search (decision D2) |
| 22 | Education center | none | Not started | Backlog (decision D4) |
| 23 | Admin dashboard / public reports | none | Not started | Backlog (decision D4) |

## 2. Problems found and fixed

### Sprint 1 audit

| Problem | Risk | Fix |
|---|---|---|
| CORS allowed every origin and also enabled credentials | Any website could call the API from a browser | Origins now come from `ALLOWED_ORIGINS` (default: local dev), credentials off |
| URL scanner fetched any address a user typed | A user could make the server request internal addresses (SSRF) | Only public `http/https` addresses, checked on every redirect; page read capped at 2MB |
| Upload was fully read into memory before the size check | Memory abuse | Read in 1MB chunks and stop at 25MB |
| A malformed model reply caused an unhandled error (HTTP 500) | Confusing failure | Now reported as a clear 502 |
| Scraped pages could carry instructions for the model | Prompt injection | Prompt treats content as data (reduces, does not remove the risk) |
| No rate limit | Free quota could be exhausted by one client | 20 requests per minute per IP (configurable) |
| No "not proof" notice in the UI | Result looked more certain than it is | Disclaimer under every result |
| Two env example files with different content | Confusion and wrong setup | `backend/.env.example` is the single source |
| Docs described a design the code does not follow | Misleading presentation | Rewrote README and `doc/` from the code |

### Sprint 2–3

| Problem | Risk | Fix |
|---|---|---|
| Verdicts came from the model's opinion alone; fact-check links were decoration | Confident but wrong or unsourced answers | New pipeline: claims → fact-checks + web search → evidence-only judge → quote validation → verdict. No evidence means `unverifiable` |
| A model can invent or alter quotes | Fake "evidence" | Every quote must appear word for word in the source it cites, or it is dropped |
| The model could claim more than its evidence shows (for example "all sources say…") | Overclaiming | The explanation is written by code from verified quotes; the model's free text is never shown |
| Missing search key silently fell back to model-only answers | Unsourced verdicts | Claims become `unverifiable` with a clear reason, and the UI shows a notice |
| Behind Render's proxy all visitors shared one rate-limit bucket | A few users could block everyone | Start command uses `--proxy-headers --forwarded-allow-ips="*"` |
| Production CORS blocked the frontend (preflight returned 400) | App unusable on a new origin | Document `ALLOWED_ORIGINS`; restart after changing `.env` |
| Dev-only demo buttons and sample data (old shape, unsourced verdict) would show on the live site | Misleading demo | Buttons appear only in dev mode; samples use the new shape |
| Source links came from the web and were rendered as-is | `javascript:` links | Only `http` and `https` links are clickable |

## 3. Gaps between the Sprint 1 presentation and the repository

| Sprint 1 deck said | Repository now | Status |
|---|---|---|
| Grok and Gemini APIs analyze text and images | Groq LLM and Whisper, plus Tavily and Google Fact Check | Resolved: deck updated to match the code (D1) |
| Deployment with Cloudflare | Render (backend) and Vercel (frontend) | Resolved: deck updated (D5) |
| Probability score, explanation, sources | Verdict per claim, code-written explanation and verified quotes; no score | Resolved (D3) |
| "Detection of AI manipulation indicators" | Claim verification; no media forensics | **Open:** planned (D2) |
| Media verification | Audio/video speech only | Open: say "speech" until forensics exists |
| Education center and admin dashboard in scope | Not started | Open: backlog (D4) |
| Cross-check with published fact-checks | Built | Resolved |

## 4. Scope decisions (team to confirm)

| ID | Decision | Outcome | Reason |
|---|---|---|---|
| D1 | AI provider | **Groq** (LLM + Whisper), plus Google Fact Check and Tavily. Gemini not used | Works, free, covers audio |
| D2 | What "media" and "detection" mean | Media = speech in audio/video. Real manipulation detection (images, video) planned as the next feature | Avoids over-claiming |
| D3 | Result model | Verdicts per claim with verified evidence; **no numeric score** | A made-up score would look precise but mean little |
| D4 | Education center and admin dashboard | Backlog; not part of Sprint 3 | Core verification came first |
| D5 | Deployment | **Render + Vercel** | Free tiers, environment-based configuration |

## 5. Evidence

- Backend tests: `cd backend && pytest` → 84 passed (offline; re-run before submitting).
- Frontend: `npm run build` succeeds. Re-run `npm run lint` after the latest changes.
- Live end-to-end test on the deployed site: passed, as reported by the team on Nov 24. Add screenshots for text, URL and media under TL-4, TL-5, TL-6, TL-13.
- Pull request: branch `feat/3-factcheck-backend` merged into `main` (add the PR link).
- Teammate review: _pending_.

Open items to record: TL-10 (responsiveness and accessibility), the status of the full logo, and a measured accuracy evaluation on labeled data.

The demo buttons in `App.jsx` (dev mode only) use sample data and example links that were not verified; they never ship in the production build.