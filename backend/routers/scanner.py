import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from models import ScanResult, UrlScanRequest, TextScanRequest
from ratelimit import rate_limit
from services import groq_service, scraper, whisper_service

router = APIRouter(
    prefix="/api/scan",
    tags=["scanner"],
    dependencies=[Depends(rate_limit)],
)

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25MB, per demo scope
ALLOWED_EXTENSIONS = {".mp4", ".mp3", ".wav", ".m4a"}
READ_CHUNK_BYTES = 1024 * 1024


@router.post("/url", response_model=ScanResult)
async def scan_url(payload: UrlScanRequest):
    """
    1) Scrape the page's main text content.
    2) Send it to Groq for claim-level fact-checking.
    """
    try:
        scraped = await scraper.scrape_url(str(payload.url))
    except scraper.ScrapeError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        result = groq_service.fact_check_text(scraped["text"])
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    if not result.source_summary:
        result.source_summary = scraped["title"]

    return result


@router.post("/text", response_model=ScanResult)
async def scan_text(payload: TextScanRequest):
    """
    Fact-check raw pasted text (a claim, headline, or historical "fact").
    """
    try:
        result = groq_service.fact_check_text(payload.text)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return result


@router.post("/media", response_model=ScanResult)
async def scan_media(file: UploadFile = File(...)):
    """
    1) Transcribe an uploaded audio/video file with Whisper.
    2) Send the transcript to Groq for fact-checking.
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Read in chunks so an oversized upload is rejected without loading it all into memory.
    chunks = []
    total = 0
    while True:
        chunk = await file.read(READ_CHUNK_BYTES)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="File exceeds the 25MB limit.")
        chunks.append(chunk)

    if total == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    file_bytes = b"".join(chunks)

    try:
        transcript = whisper_service.transcribe_file(file_bytes, file.filename or ("upload" + ext))
    except RuntimeError as e:
        # Missing/misconfigured GROQ_API_KEY: same status as the other endpoints use for this.
        raise HTTPException(status_code=502, detail=str(e))
    except whisper_service.TranscriptionError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        result = groq_service.fact_check_text(transcript)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    if not result.source_summary:
        result.source_summary = f"Transcript of {file.filename}"

    return result
