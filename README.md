# TruthLens

Media & Information Literacy detection tool — UNESCO Youth Hackathon 2026.
Paste a claim, a link, or upload a clip; TruthLens scans it and stamps a
verdict (TRUE / FALSE / MISLEADING / UNVERIFIABLE) on every factual claim it
finds.

```
truthlens/
  backend/     FastAPI — 3 endpoints: /api/scan/{url,text,media}
  frontend/    React + Vite + Tailwind — Scanner UI
```

## Quick start (local)

**1. Backend**
```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env            # then paste your GROQ_API_KEY into .env
uvicorn main:app --reload
```
Runs at `http://127.0.0.1:8000`. Interactive docs at `/docs`.

**2. Frontend** (separate terminal)
```bash
cd frontend
npm install
cp .env.example .env            # default already points at localhost:8000
npm run dev
```
Runs at `http://localhost:5173`. Open that URL — the backend must be running
too, since the frontend calls it directly.

Get a free Groq API key at **https://console.groq.com** — it powers both
fact-checking (LLM) and media transcription (hosted Whisper), so it's the
only credential you need for the whole stack.

## How it works

1. **Text** — pasted text goes straight to Groq's LLM with a fact-checking
   prompt; returns claims with verdicts and reasoning.
2. **URL** — the page is scraped (httpx + BeautifulSoup) for its main
   readable text, then fact-checked the same way. Works best on static
   article pages (Wikipedia, news sites); JS-heavy pages like YouTube won't
   scrape their real content since we don't render JavaScript.
3. **Media** — the uploaded audio/video is transcribed via Groq's hosted
   Whisper API, then the transcript is fact-checked the same way as text.

## Deployment

- **Backend** → Render (free tier). Add `GROQ_API_KEY` as an environment
  variable. No system dependencies needed (ffmpeg/torch were removed when we
  switched transcription to Groq's hosted API).
- **Frontend** → Vercel. Set root directory to `frontend`, add
  `VITE_API_URL` = your Render backend's URL.
- **Database** → none needed for this scope (Scanner-only, no persistence).

See `frontend/README.md` for frontend-specific details (project structure,
Vercel deployment steps).

## Status

- ✅ `/api/scan/text` — tested, working
- ✅ `/api/scan/url` — tested, working (best on static pages)
- ✅ `/api/scan/media` — tested, working
- ✅ Frontend — builds cleanly, wired to all three endpoints
