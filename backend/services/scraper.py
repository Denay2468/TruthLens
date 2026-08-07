"""
Fetches a URL and extracts the main readable text content for fact-checking.

Deliberately simple (BeautifulSoup, not a full headless browser) to keep the
hackathon build fast and dependency-light. Swap in Playwright later only if
you hit sites that require JS rendering.
"""

import httpx
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (compatible; TruthLensBot/1.0; +hackathon-demo)"

# Tags that are never part of readable article content
NOISE_TAGS = ["script", "style", "noscript", "nav", "footer", "header", "aside", "form", "svg"]

MAX_CHARS = 8000


class ScrapeError(Exception):
    pass


async def scrape_url(url: str) -> dict:
    """
    Fetch `url` and return {"title": str, "text": str}.
    Raises ScrapeError with a user-friendly message on failure.
    """
    headers = {"User-Agent": USER_AGENT}

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
            resp = await client.get(url)
    except httpx.TimeoutException:
        raise ScrapeError("The page took too long to respond.")
    except httpx.RequestError as e:
        raise ScrapeError(f"Could not reach that URL: {e}")

    if resp.status_code >= 400:
        raise ScrapeError(f"Page returned an error (HTTP {resp.status_code}).")

    content_type = resp.headers.get("content-type", "")
    if "text/html" not in content_type:
        raise ScrapeError("That URL doesn't appear to be a webpage (not HTML).")

    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup(NOISE_TAGS):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else url

    # Prefer <article> or <main> if present — usually the actual content,
    # not nav/sidebar/comments noise.
    main = soup.find("article") or soup.find("main") or soup.body or soup

    text = main.get_text(separator=" ", strip=True)
    text = " ".join(text.split())  # collapse whitespace

    if not text:
        raise ScrapeError("No readable text content found on that page.")

    return {"title": title, "text": text[:MAX_CHARS]}
