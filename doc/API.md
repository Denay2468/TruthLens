# TruthLens: API Documentation

**Status:** DRAFT v0.2 (Sprint 1) · matches `backend/routers/scanner.py`
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
{ "url": "https://example.com/article" }
```

### POST `/api/scan/media`

Request: `multipart/form-data` with one `file` field. Allowed extensions: `.mp4`, `.mp3`, `.wav`, `.m4a`. Maximum size: 25MB.

```bash
curl -X POST http://127.0.0.1:8000/api/scan/media -F "file=@clip.mp3"
```

## Success response (200)

```json
{
  "source_summary": "A claim about the Great Wall of China",
  "overall_note": "This is a common myth.",
  "claims": [
    {
      "text": "The Great Wall of China is visible from space with the naked eye.",
      "verdict": "false",
      "reasoning": "Astronauts report that it is not visible to the naked eye from orbit."
    }
  ]
}
```

`verdict` is one of `true`, `misleading`, `false`, `unverifiable`. The list holds at most 6 claims and can be empty when there is nothing checkable. The example values are illustrative.

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

- The Groq key is read by the backend only; clients never send or receive it.
- Long input is truncated before analysis, and the result notes it.
- **Planned (Sprint 2):** each claim may also include published fact-checks from the Google Fact Check Tools API. The fields are not final.
