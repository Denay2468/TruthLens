# TruthLens: Feature Inventory and Gap Analysis

**Task:** TL-1 Audit repository and alignment with the brief · **Status:** DRAFT for team review (Sprint 1)
**Sources compared:** repository code, README files, the Group 4 presentation (12 slides).
**Reviewer (another member):** _pending, add name and date_

## 1. Feature inventory (what the code does)

| # | Feature | Where in code | In deck? | Status | Gap or note |
|---|---|---|---|---|---|
| 1 | Text scan | `routers/scanner.py` `scan_text`; `groq_service.fact_check_text` | Yes | Working | Max 8000 characters |
| 2 | URL scan | `scan_url`; `services/scraper.py` | Yes | Working | Static HTML only (no JavaScript-rendered pages); now blocks non-public addresses |
| 3 | Media scan | `scan_media`; `services/whisper_service.py` | Yes | Working | **Audio/video speech only** (Whisper transcript). Images are not analyzed |
| 4 | Claim-level verdicts | `models.py` `Claim`, `ClaimVerdict` | Partly | Working | Deck says "probability score"; code returns `true / misleading / false / unverifiable` per claim |
| 5 | Explanation per claim | `Claim.reasoning`, `overall_note` | Yes | Working | One or two sentences |
| 6 | Sources in results | none | Yes | **Missing** | Deck promises sources; the response has no source field |
| 7 | Google Fact Check Tools lookup | none | Yes | **Missing** | Planned task TL-16 |
| 8 | Gemini API | none | Yes | **Not used** | Code uses Groq (LLM and Whisper). See decision D1 |
| 9 | AI-manipulation indicators / image analysis | none | Yes ("Detection Module") | **Missing** | The prompt checks factual claims; it does not detect AI-generated media. See decision D2 |
| 10 | Education center | none | Yes | **Not started** | Decision D4 |
| 11 | Admin dashboard / public reports | none | Yes | **Not started** | Decision D4 |
| 12 | Scanner UI (tabs, verdict stamps, scan animation) | `frontend/src` | Yes | Working | Builds and lints clean |
| 13 | "Not proof" disclaimer in UI | `ScanResults.jsx` | Yes | **Added in this audit** | Was missing |
| 14 | Rate limiting | `ratelimit.py` | Yes (NFR-2) | **Added in this audit** | In memory, per process |
| 15 | Caching | none | Yes (NFR-2) | Missing | Planned |
| 16 | API key kept server-side | `.env`, `.gitignore` | Yes | Working | Git history checked (2 commits): no keys found |
| 17 | Logo | `frontend/public/favicon.svg` only | Yes | Partial | No full logo yet (UI/UX task) |
| 18 | Responsiveness / accessibility | Tailwind, single column | Yes | Untested | TL-10 |
| 19 | Deployment configuration | none (no Dockerfile, render.yaml, vercel.json) | "Undecided" | None | Frontend README assumes Vercel + Render |
| 20 | Automated tests | `backend/tests/test_api.py` | No | **Added in this audit** | 23 offline tests |

## 2. Problems found and fixed in this audit

| Problem | Risk | Fix |
|---|---|---|
| CORS allowed every origin and also enabled credentials | Any website could call the API from a browser; the combination is invalid in browsers | Origins now come from `ALLOWED_ORIGINS` (default: local dev), credentials off |
| URL scanner fetched any address a user typed | A user could make the server request internal addresses (SSRF) | Only public `http/https` addresses, checked on every redirect; page read capped at 2MB |
| Upload was fully read into memory before the size check | Memory abuse | Read in 1MB chunks and stop at 25MB |
| A malformed model reply caused an unhandled error (HTTP 500) | Confusing failure | Now reported as a clear 502 |
| Scraped pages could carry instructions for the model | Prompt injection | Prompt tells the model to treat content as data (reduces, does not remove the risk) |
| No rate limit | Free quota could be exhausted by one client | 20 requests per minute per IP (configurable) |
| No "not proof" notice in the UI | Result looked more certain than it is | Disclaimer under every result |
| Two env example files with different content; root one listed variables the code never reads | Confusion and wrong setup | Removed the root file; `backend/.env.example` is the single source |
| Docs described a design the code does not follow | Misleading presentation | Rewrote README and `doc/` from the actual code |

## 3. Gaps between the presentation and the repository

| Deck says | Repository does | Proposed fix |
|---|---|---|
| Gemini API analyzes text and images | Groq LLM analyzes text; Groq Whisper transcribes audio/video | Update the deck to Groq (D1) |
| Probability score, explanation, sources | Verdict + reasoning per claim; no score; no sources | Say "claim-level verdicts with explanations" now; add sources with the Fact Check integration (D3) |
| Detection of AI manipulation indicators | Fact-checking of claims | Rename the module "Claim fact-checking" or add a real detector later (D2) |
| Media verification | Audio/video speech only | Say "audio/video (speech)" (D2) |
| Education center, admin dashboard in scope | Not started | Team decision (D4) |
| Cross-check with published fact-checks | Not built | Keep as Sprint 2 plan |

## 4. Scope decisions (proposed, the team must confirm)

| ID | Decision | Proposal | Reason |
|---|---|---|---|
| D1 | AI provider | **Keep Groq** (LLM + Whisper) and **add** Google Fact Check Tools. Treat Gemini as optional later (for images) | It already works, is free, and covers audio. Switching costs time and drops transcription |
| D2 | What "media" and "detection" mean | Define media as audio/video speech for now; rename the module to claim fact-checking | Matches the real behavior; avoids over-claiming |
| D3 | Result model | Keep verdicts per claim; show the numeric score only if the team defines how it is computed | A made-up score would look precise but mean little |
| D4 | Education center and admin dashboard | Mark as **stretch goals** unless the team has capacity in Sprint 2 | Not started; core scanner and Fact Check come first |
| D5 | Deployment | Decide before Sprint 3 | Frontend README assumes Vercel + Render |

## 5. Evidence

- Backend tests: `cd backend && pytest` → 23 passed (offline).
- Frontend: `npm run build` succeeds; `npm run lint` reports 0 warnings and 0 errors.
- Git history: 2 commits scanned for key patterns; none found.
- Commit/PR link: _add after pushing the branch `chore/sprint1-audit-fixes`_
- Teammate review: _pending_

Not verified (needs a real key and internet): live calls to Groq, real URL scraping of public sites, and media transcription. Test these manually and record the results under TL-4, TL-5 and TL-6.
