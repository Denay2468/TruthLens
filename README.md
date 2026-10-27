# TruthLens

Digital manipulation detection and information verification platform.
**Group 4 · IT Project Management · Status: Sprint 1 in progress (Oct 19–30, 2026)**

TruthLens lets a user paste a claim, submit a link, or upload an audio/video clip. It extracts the main factual claims and gives each one a verdict (`true`, `misleading`, `false` or `unverifiable`) with a short explanation.
Results are AI-generated **estimates**. They are **not proof** and **not legal evidence**.

## What works today

| Feature | Status |
|---|---|
| Text scan: paste a claim, headline or paragraph | Working |
| URL scan: scrape a web page and fact-check its text | Working |
| Media scan: transcribe audio/video (mp4, mp3, wav, m4a, up to 25MB) and fact-check the transcript | Working |
| Claim-level verdicts and reasoning in the UI | Working |
| Google Fact Check Tools lookup (published fact-checks as evidence) | Planned, Sprint 2 |
| Education center and admin dashboard | Not started |

See [`doc/FEATURE_INVENTORY.md`](doc/FEATURE_INVENTORY.md) for the full list, gaps and scope decisions.

## Tech stack

- **Backend:** Python, FastAPI, httpx, BeautifulSoup, Groq API (LLM `openai/gpt-oss-20b` for fact-checking, `whisper-large-v3-turbo` for transcription)
- **Frontend:** React 19, Vite, Tailwind CSS 4

## Project structure

```
TruthLens/
├── backend/
│   ├── main.py               FastAPI app, CORS, health check
│   ├── models.py             Request and response models
│   ├── ratelimit.py          Per-IP rate limiter
│   ├── routers/scanner.py    /api/scan/text, /url, /media
│   ├── services/             groq_service, whisper_service, scraper
│   └── tests/                Offline tests (no API calls)
├── frontend/                 React scanner UI
└── doc/                      Architecture, API, requirements, inventory, Postman collection
```

## Run it locally

You need **Python 3.10+**, **Node.js 18+** and a free **Groq API key** from <https://console.groq.com>.

**1. Backend** (from the repository root):

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate      # macOS / Linux
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env
# open .env and set GROQ_API_KEY
uvicorn main:app --reload
```

The API runs at <http://127.0.0.1:8000>. Interactive docs: <http://127.0.0.1:8000/docs>.

**2. Frontend** (in a second terminal):

```bash
cd frontend
npm install
cp .env.example .env            # Windows: copy .env.example .env
npm run dev
```

Open <http://localhost:5173>.

## Run the tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

The tests replace Groq with a fake, so they run offline and cost nothing.

## Configuration

| Variable | Where | Purpose |
|---|---|---|
| `GROQ_API_KEY` | `backend/.env` | Groq key (required, server-side only) |
| `GROQ_MODEL` | `backend/.env` | Optional model override |
| `ALLOWED_ORIGINS` | `backend/.env` | Comma-separated browser origins allowed to call the API (default: local dev only) |
| `RATE_LIMIT_PER_MINUTE` | `backend/.env` | Requests per client IP per minute (default 20, `0` disables) |
| `VITE_API_URL` | `frontend/.env` | Backend URL (default `http://127.0.0.1:8000`) |

Never commit a `.env` file. If a key is ever committed, rotate it in the Groq console immediately.

## Documentation

- [`doc/ARCHITECTURE.md`](doc/ARCHITECTURE.md): components, data flow, security
- [`doc/API.md`](doc/API.md): endpoints, requests, responses, errors
- [`doc/REQUIREMENTS.md`](doc/REQUIREMENTS.md): requirements and their status
- [`doc/FEATURE_INVENTORY.md`](doc/FEATURE_INVENTORY.md): repository audit, gaps and scope decisions
- [`doc/postman/`](doc/postman): Postman collection for the backend

## Project management

- Task tracker: Notion (TruthLens Task Tracker)
- Sprints: 1 (Oct 19–30), 2 (Nov 2–13), 3 (Nov 16–27)
- Deployment: design under discussion, to be decided before Sprint 3

## Team

| Role | Member |
|---|---|
| Project Manager | Izzul Maulanal Haqqi |
| Frontend Dev | Andhika Ryan Setito, Dev Alldino Zain |
| DevOps Engineer | De Nay Aung |
| Backend Dev | Deva Aditya Sayputra, Bintang Aulia Farhantika |
| UI/UX | Naufal Arif AThallah |
