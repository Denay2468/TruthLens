# TruthLens — Frontend (Scanner UI)

React + Vite + Tailwind frontend for the TruthLens Scanner. Three input modes
(text, URL, media upload) that call your FastAPI backend and display
color-stamped fact-check verdicts.

## Design

A "digital forensics scanner" aesthetic — ink-navy background, phosphor-green
scan accents, verdict badges styled as rotated ink stamps (TRUE / FALSE /
MISLEADING / UNVERIFIABLE). A scan-beam animation sweeps across the results
panel while a request is in flight.

## Where this goes in your repo

Drop this folder in as `frontend/` alongside your existing `backend/` folder,
matching the structure from your original plan:
```
your-repo/
  backend/     <- already built
  frontend/    <- this folder
```

## Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Point it at your backend**:
   ```bash
   cp .env.example .env
   ```
   The default (`http://127.0.0.1:8000`) already matches your local backend —
   you only need to edit `.env` once you deploy the backend to Render and
   want the frontend to call the live URL instead.

3. **Run it locally**:
   ```bash
   npm run dev
   ```
   Open the URL it prints (usually `http://localhost:5173`).

   Make sure your backend is also running (`uvicorn main:app --reload` in
   `backend/`) — the frontend calls it directly from the browser.

## Project structure

```
src/
  App.jsx                Top-level layout, wires input -> API -> results
  lib/api.js              Fetch wrappers for the 3 scan endpoints
  components/
    ScanInput.jsx           Tab switcher + text/URL/file inputs
    ScanResults.jsx         Results panel (loading / error / empty / claims)
    ScanBeam.jsx             Signature scan animation shown while loading
    ClaimCard.jsx            One claim's text + reasoning
    VerdictStamp.jsx         The rotated ink-stamp verdict badge
```

## Deployment (Vercel)

1. Push this repo to GitHub (if not already).
2. In Vercel, import the repo, set the **root directory** to `frontend`.
3. Add an environment variable: `VITE_API_URL` = your Render backend URL
   (e.g. `https://truthlens-api.onrender.com`).
4. Deploy. Vercel auto-detects Vite and runs `npm run build`.

## Notes

- No component library — plain Tailwind utility classes + a handful of CSS
  custom properties in `index.css` for the color tokens, so there's nothing
  extra to install or configure.
- The 25MB upload limit is not checked in the browser. The backend enforces it
  and the UI shows its error message if a file is too big.
- Reduced-motion is respected (scan/stamp animations disable automatically
  if the user has that OS setting on).
