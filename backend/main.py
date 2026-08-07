from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import scanner

app = FastAPI(
    title="TruthLens API",
    description="Media & Information Literacy detection tools — URL, media, and text fact-checking.",
    version="0.1.0",
)

# Allow the frontend (Vercel deployment + local dev) to call this API.
# Tighten allow_origins to your actual frontend domain before going live.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scanner.router)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "truthlens-api"}
