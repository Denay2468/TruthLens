# TruthLens: API Documentation

**Status:** DRAFT v0.3 (Sprint 2) · matches `backend/routers/scanner.py`
Base URL (local): `http://127.0.0.1:8000` · Interactive docs: `/docs` · Postman: `doc/postman/`

All scan endpoints live under `/api/scan` and return the same result shape. They are rate limited per client IP (default 20 per minute).

## Endpoints

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Health check |
| POST | `/api/scan/text` | Fact-check pasted text |
| POST | `/api/scan/url` | Scrape a web page and fact-check its text |
| POST | `/api/scan/media` | Transcribe an audio/video file and fact-check the transcript |

### GET `/`

```json
{ "status": "ok", "service": "truthlens-api" }
```

### POST `/api/scan/text`

Request (JSON): `text` is required, 1–8000 characters.

```json
{ "text": "The Great Wall of China is visible from space." }
```

### POST `/api/scan/url`

Request (JSON): `url` must be a valid public `http` or `https` URL.

```json
{ "url": "[https://example.com/article](https://example.com/article)" }
```

### POST `/api/scan/media`

Request: `multipart/form-data` with one `file` field. Allowed extensions: `.mp4`, `.mp3`, `.wav`, `.m4a`. Maximum size: 25MB.

```bash
curl -X POST [http://127.0.0.1:8000/api/scan/media](http://127.0.0.1:8000/api/scan/media) -F "file=@clip.mp3"
```

## Success response (200)

```json
{
  "source_summary": "A claim about the Great Wall of China",
  "overall_note": "This is a common myth.",
  "fact_check_status": "ok",
  "claims": [
    {
      "text": "The Great Wall of China is visible from space with the naked eye.",
      "verdict": "false",
      "reasoning": "Astronauts report that it is not visible to the naked eye from orbit.",
      "fact_checks": [
        {
          "publisher": "Reuters",
          "rating": "False",
          "url": "[https://www.reuters.com/fact-check/great-wall-space](https://www.reuters.com/fact-check/great-wall-space)",
          "title": "Fact Check: The Great Wall of China is not visible from space with the naked eye",
          "review_date": "2024-01-15T00:00:00Z"
        }
      ]
    }
  ]
}
```

- `verdict` is one of `true`, `misleading`, `false`, `unverifiable`. Groq remains the sole source of the verdict; published fact-checks are attached strictly as supporting evidence.
- `claims` holds at most 6 claims and can be empty when there is nothing checkable.
- `fact_checks` defaults to `[]` when no published fact-check matches the claim (this is normal, not an error). Each item contains `publisher`, `rating`, `url`, `title`, and optional `review_date` (ISO 8601).
- `fact_check_status` reports the overall state of the Google Fact Check Tools API lookup:
  - `"ok"`: every lookup completed (whether matches were found or not).
  - `"not_configured"`: `GOOGLE_FACTCHECK_API_KEY` is not set; Groq verdicts are still returned with empty `fact_checks`.
  - `"unavailable"`: one or more lookups timed out, hit a rate limit, or errored; the scan still succeeds with Groq's verdicts and empty `fact_checks` for failed lookups.
- The example values above are illustrative.

## Errors

Errors return `{ "detail": "message" }`.

| Status | When |
|---|---|
| 400 | Uploaded file is empty |
| 413 | File is larger than 25MB |
| 415 | File type is not allowed |
| 422 | Invalid input; page could not be fetched or is not HTML; address not allowed; no speech found |
| 429 | Too many requests from this IP |
| 502 | Groq request failed, `GROQ_API_KEY` is missing, or the model returned unusable output |

## Notes

- Both `GROQ_API_KEY` and `GOOGLE_FACTCHECK_API_KEY` are read by the backend only; clients never send or receive them.
- `GOOGLE_FACTCHECK_API_KEY` is optional. If omitted or if the Google Fact Check Tools API fails, scan endpoints still return `200 OK` using the Groq result.
- Long input is truncated before analysis, and the result notes it.