# TruthLens: Requirements Specification

**Status:** v1.0 (Sprint 3, Nov 16–27, 2026) · Notion copy: keep in sync with this file

## 1. Purpose

Manipulated and misleading content spreads quickly, and most people cannot easily check what is real. TruthLens gives one place to submit text, a link or an audio/video clip and get claim-level verdicts that are **backed by source quotes the system has verified**. It also aims to build digital literacy. Results are not proof and not legal evidence: sources can be wrong or out of date, so users are pointed to the original links.

## 2. Goals

| # | Goal | Status |
|---|---|---|
| G1 | Objective verification: check claims against published fact-checks and web sources, and show the evidence | Met for text claims. Detection of manipulated images or video is **not** built |
| G2 | Public education: help people judge information critically | Partly: the UI shows quotes and links so users can check for themselves. No education center yet |
| G3 | Digital security: help prevent loss from fraud that uses misleading content | Partly: verification of claims only |

## 3. Scope

**In scope:** web portal for text, URL and media (speech); claim verification module; education center and admin dashboard (backlog, not started).
**Out of scope:** native mobile app (responsive web only), voice calls, encrypted messages, legal investigation, and, for Sprint 3, image/video manipulation forensics (planned next).

## 4. Functional requirements

| ID | Requirement | Component | Status today |
|---|---|---|---|
| FR-1 | Submit text, a URL, or audio/video for verification | Web portal | Implemented (media means speech in audio/video) |
| FR-2 | Look up existing published fact-checks | Google Fact Check Tools API (`factcheck_service.py`) | Implemented (optional key) |
| FR-3 | Extract checkable claims and judge each one using only the sources it is given | Groq LLM (`judge_service.py`) | Implemented |
| FR-4 | Return an explained result with sources | Verification pipeline | Implemented: verified quotes with source links and a code-written explanation. No numeric score, by design (decision D3) |
| FR-5 | Publish anti-hoax literacy articles | Education center | Not started (backlog) |
| FR-6 | Manage public reports | Admin dashboard | Not started (backlog) |
| FR-7 | Gather web evidence for each claim | Tavily search (`evidence_service.py`) | Implemented (optional key; without it claims stay `unverifiable`) |
| FR-8 | Detect manipulation in images and video | Forensics module | Not started. Planned: metadata, C2PA Content Credentials, reverse image search |

### Verdict rules (FR-3, FR-4)

The model proposes a verdict, but code limits it by the quotes that survive verification:

| Verdict | Requires |
|---|---|
| `true` | at least one verified supporting quote and no refuting quote |
| `false` | at least one verified refuting quote and no supporting quote |
| `misleading` | at least one verified supporting or refuting quote |
| `unverifiable` | everything else, including "no sources found" |

A quote counts only if it appears word for word in the source it cites.

## 5. Non-functional requirements

| ID | Requirement | Status today |
|---|---|---|
| NFR-1 | Responsive, simple UX | Partial: single-column layout built; responsiveness and accessibility testing (TL-10) must be recorded |
| NFR-2 | API keys server-side; rate limiting and caching | Keys and rate limiting implemented; caching not implemented |
| NFR-3 | Honest communication of uncertainty | Implemented: no evidence means `unverifiable`; every firm verdict shows its quotes; notices when searches are off or failed; disclaimer under every result |
| NFR-4 | Reasonable response time | Not measured formally. A scan makes one extraction call, up to 5 searches and up to 5 judge calls; the free Render backend can take about a minute to wake up |
| NFR-5 | Basic input safety | Implemented: size, type and length limits; URL safety checks (private addresses blocked on every redirect); quote validation; offline tests in `backend/tests` |
| NFR-6 | Privacy-minded handling | Nothing is stored by TruthLens. Claim text is sent to Groq, Tavily and Google Fact Check, and uploads to Groq for transcription; this should be stated to users |
| NFR-7 | Verifiability | Implemented: each non-`unverifiable` verdict carries clickable, verified quotes |
| NFR-8 | Availability for demos | Partial: free-tier hosting sleeps when idle; open the backend URL shortly before a demo |

## 6. Constraints and assumptions

- Free tiers only. Groq, Tavily and Google limits can change; check each console. One scan can use up to 5 searches.
- Verdicts rest on what the search returns: short snippets, with no weighting of source reliability yet.
- Some websites block automated fetching (HTTP 403), so URL scans of those sites fail with a clear message.
- Deployment: backend on Render, frontend on Vercel (decided).

## 7. Risks

| Risk | Mitigation |
|---|---|
| Free quota runs out during a demo | Rate limit (set to 5 per minute per IP in production), `JUDGE_CONCURRENCY`, short demo inputs, usage dashboards checked before demos |
| Wrong verdicts | No evidence gives `unverifiable`; quotes checked against the source text; verdicts capped by verified quotes; disclaimer in the UI |
| Unreliable or outdated sources | **Open risk:** source reliability is not weighted yet. Planned: credibility weighting and a requirement for independent sources |
| Prompt injection through scraped pages or search results | Both prompts treat content as data; code-side rules still cap the verdict. Reduces, does not remove, the risk |
| URL scans blocked by websites | Clear error message; fallback extraction planned |
| Over-claiming (people expect deepfake detection) | UI and slides say media scans check speech only; forensics is listed as planned |
| Key leak | `.env` ignored by git; keys only in Render's environment; rotate on any exposure |
| Free backend asleep during a demo | Open the backend URL a minute before; keep screenshots as a backup |

## 8. Traceability to tests

| Requirement | Test |
|---|---|
| FR-1 | `backend/tests/test_api.py` (text, URL, media endpoints); manual checks TL-4, TL-5, TL-6 |
| FR-2 | `backend/tests/test_factcheck_service.py` |
| FR-3, FR-4 | `backend/tests/test_judge_service.py` (quote validation, verdict caps, fabricated quotes, injected instructions), `test_pipeline.py` |
| FR-7 | `backend/tests/test_evidence_service.py` |
| NFR-2, NFR-5 | rate limit, upload and SSRF tests in `test_api.py`; TL-7, TL-8 |
| NFR-3 | `test_api.py` (no-key and failed-search cases), `test_pipeline.py` |
| NFR-1 | TL-10 (record the result) |
| FR-5, FR-6, FR-8 | none: not started |

Run all offline tests with `cd backend && pytest` (84 tests when last run).