import os

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import scanner

app = FastAPI(
    title="TruthLens API",
    description="Media & Information Literacy detection tools: URL, media, and text fact-checking.",
    version="0.1.0",
)

# Allowed browser origins. Set ALLOWED_ORIGINS (comma-separated) in .env for the
# deployed frontend, e.g. ALLOWED_ORIGINS=https://truthlens.vercel.app
# The default only allows local development.
DEFAULT_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
allowed_origins = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",")
    if o.strip()
]

# The API uses no cookies or sessions, so credentials stay off. (Browsers also
# reject the combination of allow_origins=["*"] with credentials.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(scanner.router)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "truthlens-api"}
