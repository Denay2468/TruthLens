# TruthLens: API Documentation

**Status:** v1.0 (Sprint 3) · matches `backend/routers/scanner.py` and `backend/services/pipeline.py`
Base URL (local): `http://127.0.0.1:8000` · Interactive docs: `/docs` · Postman: `doc/postman/`

All scan endpoints live under `/api/scan` and return the same result shape. They are rate limited per client IP (default 20 per minute).

## Endpoints

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Health check |
| POST | `/api/scan/text` | Verify the claims in pasted text |
| POST | `/api/scan/url` | Fetch a web page and verify its claims |
| POST | `/api/scan/media` | Transcribe an audio/video file and verify the transcript |

### GET `/`

```json
{ "status": "ok", "service": "truthlens-api" }
```

### POST `/api/scan/text`

Request (JSON): `text` is required, 1–8000 characters.

```json
{ "text": "Drinking hot water with lemon cures COVID-19." }
```

### POST `/api/scan/url`

Request (JSON): `url` must be a valid public `http` or `https` URL.

```json
{ "url": "https://en.wikipedia.org/wiki/Mount_Merapi" }
```

### POST `/api/scan/media`

Request: `multipart/form-data` with one `file` field. Allowed extensions: `.mp4`, `.mp3`, `.wav`, `.m4a`. Maximum size: 25MB. Only speech is analyzed.

```bash
curl -X POST http://127.0.0.1:8000/api/scan/media -F "file=@clip.mp3"
```

## Success response (200)

```json
{
  "source_summary": "A claim that hot water with lemon cures COVID-19",
  "overall_note": "Checked 1 claim against sources: 1 false.",
  "fact_check_status": "ok",
  "evidence_status": "ok",
  "claims": [
    {
      "text": "Drinking hot water with lemon cures COVID-19",
      "verdict": "false",
      "reasoning": "Verified quotes from 3 sources contradict this claim, including 1 published fact-check.",
      "evidence": [
        {
          "url": "https://apnews.com/article/example",
          "title": "Example title",
          "quote": "The drink is not a cure for the coronavirus.",
          "stance": "refutes",
          "source_type": "web",
          "retrieved_at": "2026-11-24T10:00:00+00:00"
        }
      ],
      "fact_checks": []
    }
  ]
}
```

The example values are illustrative.

### Fields

| Field | Meaning |
|---|---|
| `source_summary` | One sentence on what was analyzed |
| `overall_note` | Written by code: claim counts by verdict, plus notes about failed searches or truncation |
| `fact_check_status` | `ok`, `not_configured` (no Google key) or `unavailable` (lookup failed) |
| `evidence_status` | `ok`, `not_configured` (no Tavily key) or `unavailable` (at least one search failed) |
| `claims` | At most 5 claims; can be empty when nothing is checkable |
| `claims[].verdict` | `true`, `misleading`, `false` or `unverifiable` |
| `claims[].reasoning` | Written by code from the verified quotes. The model's own explanation is never returned |
| `claims[].evidence[]` | Verified quotes (max 4 per claim). Each quote appears word for word in the source at `url` |
| `evidence[].stance` | `supports`, `refutes` or `neutral` |
| `evidence[].source_type` | `web` (search result) or `fact_check` (published fact-check) |
| `claims[].fact_checks[]` | Published fact-checks found for the claim (publisher, rating, title, url) |

### How verdicts are decided

The model proposes a verdict, but it can never go further than its verified quotes allow:

| Verdict | Requires |
|---|---|
| `true` | at least one supporting quote and no refuting quote |
| `false` | at least one refuting quote and no supporting quote |
| `misleading` | at least one supporting or refuting quote |
| anything else | `unverifiable` |

A claim with no sources at all is `unverifiable` without calling the model. Quotes shorter than 12 characters are rejected.

## Errors

Errors return `{ "detail": "message" }`.

| Status | When |
|---|---|
| 400 | Uploaded file is empty |
| 413 | File is larger than 25MB |
| 415 | File type is not allowed |
| 422 | Invalid input; page could not be fetched (for example HTTP 403) or is not HTML; address not allowed; no speech found |
| 429 | Too many requests from this IP |
| 502 | Groq request failed, `GROQ_API_KEY` is missing, or the model returned unusable output |

A failed web search or fact-check lookup is **not** an error: the scan still returns 200, the affected claims become `unverifiable`, and `evidence_status` / `fact_check_status` say what happened.

## Notes

- API keys are read by the backend only; clients never send or receive them.
- Long input is truncated to 6000 characters before analysis, and `overall_note` says so.
- Page text from URL scans is cut to 8000 characters before that.
- Fact-check lookups run concurrently with a 5 second timeout and return at most 3 results per claim.