# TruthLens: Requirements Specification

**Status:** DRAFT v0.2 (Sprint 1, Oct 19–30, 2026) · Notion copy: keep in sync with this file

## 1. Purpose

Manipulated and misleading content spreads quickly, and most people cannot easily check what is real. TruthLens gives one place to submit text, a link or an audio/video clip and get claim-level verdicts with explanations. It also aims to build digital literacy. Results are estimates, not proof and not legal evidence.

## 2. Goals

| # | Goal |
|---|---|
| G1 | Objective detection: fast analysis of claims, cross-checked against published fact-checks (cross-checking is planned) |
| G2 | Public education: help people judge information critically |
| G3 | Digital security: help prevent loss from fraud that uses misleading content |

## 3. Scope

**In scope:** web portal for text, URL and media; detection module; education center; admin dashboard.
**Out of scope:** native mobile app (responsive web only), voice calls, encrypted messages, legal investigation.

## 4. Functional requirements

| ID | Requirement | Component | Status today |
|---|---|---|---|
| FR-1 | Submit text, a URL, or audio/video for verification | Web portal | Implemented (media means audio/video) |
| FR-2 | Look up existing published fact-checks | Google Fact Check Tools API | Planned (Sprint 2) |
| FR-3 | Analyze content with AI | Groq LLM | Implemented (claim extraction and verdicts) |
| FR-4 | Return an explained result with sources | Detection module | Partial: verdict and reasoning yes; numeric score and sources not yet |
| FR-5 | Publish anti-hoax literacy articles | Education center | Not started |
| FR-6 | Manage public reports | Admin dashboard | Not started |

## 5. Non-functional requirements

| ID | Requirement | Status today |
|---|---|---|
| NFR-1 | Responsive, simple UX | Partial: single-column layout built; responsiveness and accessibility not yet tested (TL-10) |
| NFR-2 | API key server-side; rate limiting and caching | Key and rate limiting implemented; caching not implemented |
| NFR-3 | Honest communication of uncertainty | Implemented: a disclaimer is shown under every result |
| NFR-4 | Reasonable response time | Not measured yet |
| NFR-5 | Basic input safety | Implemented: size, type and length limits; URL safety checks; tests in `backend/tests` |
| NFR-6 | Privacy-minded handling | Nothing is stored; uploads are held in memory only during the request |

## 6. Constraints and assumptions

- Free tiers only; Groq limits can change (check the Groq console).
- Verdicts come from a language model without live web access.
- Deployment design is undecided.

## 7. Risks

| Risk | Mitigation |
|---|---|
| Free quota runs out during a demo | Rate limiting now; caching planned; short demo inputs |
| Wrong verdicts | Disclaimer in the UI; fact-check evidence planned; human review of demo examples |
| Prompt injection through scraped pages | Prompt hardening in place; limits documented |
| Key leak | `.env` ignored by git; rotate on any exposure |

## 8. Traceability to tests

| Requirement | Test |
|---|---|
| FR-1, FR-3 | `backend/tests/test_api.py` (text, URL, media); TL-4, TL-5, TL-6 manual checks |
| NFR-2, NFR-5 | `test_rate_limit_returns_429`, upload and SSRF tests; TL-7, TL-8 |
| NFR-1 | TL-10 (not done yet) |
