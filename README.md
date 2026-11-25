# TruthLens

Digital manipulation detection and information verification platform.
**Group 4 · IT Project Management · Status: Sprint 3 (Nov 16–27, 2026)**

**Live demo:** <https://truthlens-blush-seven.vercel.app>

TruthLens lets a user paste a claim, submit a link, or upload an audio/video clip. It extracts the main factual claims and checks each one **against real sources**. Every verdict (`true`, `misleading`, `false` or `unverifiable`) comes with source quotes that the backend has verified word for word. If no evidence is found, the verdict is `unverifiable`. The system never guesses.

Results are **not proof** and **not legal evidence**. Sources can be wrong or out of date: open the links and judge for yourself.

## How a claim is verified

```
extract claims  →  published fact-checks + web search (in parallel)
                →  evidence-only judge  →  quote validation  →  verdict + proof
```

1. **Extract:** an LLM splits the text into checkable claims (no verdicts at this step).
2. **Gather evidence:** the Google Fact Check Tools API and a Tavily web search run side by side.
3. **Judge:** the LLM reads only the numbered sources it is given and must quote them, labeling each quote `supports`, `refutes` or `neutral`.
4. **Validate:** the code drops any quote that does not appear word for word in the source it cites, and caps the verdict at what the surviving quotes allow.
5. **Explain:** the explanation shown to the user is written by code from the verified quotes. The model's own free text is never shown.

## What works today

| Feature | Status |
|---|---|
| Text scan: paste a claim, headline or paragraph | Working |
| URL scan: fetch a web page and verify its claims | Working (sites that block bots return a clear error) |
| Media scan: transcribe audio/video (mp4, mp3, wav, m4a, up to 25MB) and verify the transcript | Working (speech only) |
| Source-backed verdicts with clickable, verified quotes | Working |
| Google Fact Check Tools lookup | Working (optional key) |
| Web evidence search (Tavily) | Working (optional key; without it claims stay `unverifiable`) |
| Image and video manipulation detection | **Not built.** Planned next (see below) |
| Education center and admin dashboard | Not started |

See [`doc/FEATURE_INVENTORY.md`](doc/FEATURE_INVENTORY.md) for the full list and scope decisions.

## Tech stack

- **Backend:** Python, FastAPI, httpx, BeautifulSoup, Groq API (`openai/gpt-oss-20b` for claims and judging, `whisper-large-v3-turbo` for transcription), Tavily search, Google Fact Check Tools API
- **Frontend:** React 19, Vite, Tailwind CSS 4
- **Hosting:** Render (backend), Vercel (frontend)

## Project structure

```
TruthLens/
├── backend/
│   ├── main.py                 FastAPI app, CORS, health check
│   ├── models.py               Request and response models
│   ├── ratelimit.py            Per-IP rate limiter
│   ├── routers/scanner.py      /api/scan/text, /url, /media
│   ├── services/
│   │   ├── pipeline.py         Chains the verification steps
│   │   ├── judge_service.py    Claim extraction, evidence-only judge, quote validation
│   │   ├── evidence_service.py Web search (Tavily)
│   │   ├── factcheck_service.py Google Fact Check lookup
│   │   ├── scraper.py          Page fetching with SSRF protection
│   │   ├── whisper_service.py  Audio/video transcription
│   │   └── groq_service.py     Legacy single-call checker (kept for its model setting)
│   ├── tests/                  Offline tests (no API calls)
│   └── try_step3.py            Manual end-to-end check with real keys
├── frontend/                   React scanner UI
└── doc/                        Architecture, API, requirements, inventory, Postman collection
```

## Run it locally

You need **Python 3.10+**, **Node.js 18+** and a free **Groq API key** from <https://console.groq.com>. A **Tavily key** (<https://tavily.com>) and a **Google Fact Check key** are optional but needed for real verdicts.

**1. Backend** (from the repository root):

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate      # macOS / Linux
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env
# open .env and set GROQ_API_KEY (and the optional keys)
uvicorn main:app --reload
```

The API runs at <http://127.0.0.1:8000>. Interactive docs: <http://127.0.0.1:8000/docs>.
Restart uvicorn after you change `.env`: `--reload` only watches `.py` files.

**2. Frontend** (in a second terminal):

```bash
cd frontend
npm install
cp .env.example .env            # Windows: copy .env.example .env
npm run dev
```

Open <http://localhost:5173>. The "Test UI" demo buttons appear in dev mode only.

**3. Try the whole pipeline from the command line:**

```bash
cd backend
python try_step3.py "Drinking hot water with lemon cures COVID-19."
```

## Run the tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

84 tests run offline: Groq, Tavily and Google are replaced with fakes, so they cost nothing.

## Configuration

| Variable | Where | Purpose |
|---|---|---|
| `GROQ_API_KEY` | `backend/.env` | Groq key (required, server-side only) |
| `GROQ_MODEL` | `backend/.env` | Optional model override (try `openai/gpt-oss-120b` if quotes are often rejected) |
| `TAVILY_API_KEY` | `backend/.env` | Web evidence search. Without it, claims are `unverifiable` unless a fact-check is found |
| `GOOGLE_FACTCHECK_API_KEY` | `backend/.env` | Published fact-checks (optional) |
| `GOOGLE_FACTCHECK_LANGUAGE_CODE` | `backend/.env` | Optional, e.g. `en`; unset means all languages |
| `JUDGE_CONCURRENCY` | `backend/.env` | Claims judged at once (default 3, protects free-tier rate limits) |
| `ALLOWED_ORIGINS` | `backend/.env` | Comma-separated browser origins allowed to call the API (default: local dev only) |
| `RATE_LIMIT_PER_MINUTE` | `backend/.env` | Requests per client IP per minute (default 20, `0` disables) |
| `VITE_API_URL` | `frontend/.env` | Backend URL (default `http://127.0.0.1:8000`). Baked in at build time: redeploy after changing it |

Never commit a `.env` file. If a key is ever committed, rotate it in the provider's console immediately.

## Deployment

- **Backend (Render):** set the environment variables above. Set `ALLOWED_ORIGINS` to the exact Vercel URL (with `https://`, no trailing slash). Start command:
  `uvicorn main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"`
  (the proxy flags let the rate limiter see real client IPs behind Render's proxy). The free tier sleeps: open the health URL a minute before a demo.
- **Frontend (Vercel):** set `VITE_API_URL` to the Render URL, then redeploy.

## Known limitations

- Source reliability is not weighted: one refuting quote from a weak source can still produce `false`.
- Search snippets are short, so some true claims come back `unverifiable`.
- Some websites block automated fetching (HTTP 403); a fallback is planned.
- Images and video frames are **not analyzed**. Media scans only check what is said.
- Accuracy has not been measured on a labeled dataset yet.

## Next steps

1. Image forensics: metadata, C2PA Content Credentials, reverse image search.
2. Source credibility weighting.
3. Fallback page extraction for sites that block the scraper.
4. Accuracy evaluation on labeled data.

## Documentation

- [`doc/ARCHITECTURE.md`](doc/ARCHITECTURE.md): components, data flow, security
- [`doc/API.md`](doc/API.md): endpoints, requests, responses, errors
- [`doc/REQUIREMENTS.md`](doc/REQUIREMENTS.md): requirements and their status
- [`doc/FEATURE_INVENTORY.md`](doc/FEATURE_INVENTORY.md): repository audit, gaps and scope decisions
- [`doc/postman/`](doc/postman): Postman collection for the backend

## Project management

- Task tracker: Notion (TruthLens Task Tracker)
- Sprints: 1 (Oct 19–30), 2 (Nov 2–13), 3 (Nov 16–27)

## Team

| Role | Member |
|---|---|
| Project Manager | Izzul Maulanal Haqqi |
| Frontend Dev | Andhika Ryan Setito, Dev Alldino Zain |
| DevOps Engineer | De Nay Aung |
| Backend Dev | Deva Aditya Sayputra, Bintang Aulia Farhantika |
| UI/UX | Naufal Arif Athallah |