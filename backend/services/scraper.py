"""
Fetches a URL and extracts the main readable text content for fact-checking.

Deliberately simple (BeautifulSoup, not a full headless browser) to keep the
build fast and dependency-light. Swap in Playwright later only if you hit
sites that require JS rendering.

Security: because users can submit any URL, the scraper refuses non-http(s)
links and addresses that are not public (localhost, private networks, cloud
metadata addresses). The check runs on every redirect hop. Known limitation:
a hostile DNS server could still change its answer between the check and the
request (DNS rebinding); a hardened deployment should also restrict egress
at the network level.
"""

import asyncio
import ipaddress
import socket
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (compatible; TruthLensBot/1.0; +student-project)"

# Tags that are never part of readable article content
NOISE_TAGS = ["script", "style", "noscript", "nav", "footer", "header", "aside", "form", "svg"]

MAX_CHARS = 8000
MAX_BYTES = 2 * 1024 * 1024  # stop reading a page after 2MB


class ScrapeError(Exception):
    pass


def _check_public_url_sync(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ScrapeError("Only http and https links are supported.")
    host = parsed.hostname
    if not host:
        raise ScrapeError("That URL has no valid host.")

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise ScrapeError("Could not resolve that address.")

    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise ScrapeError("That address is not allowed.")


async def _assert_public_url(url: str) -> None:
    # getaddrinfo blocks, so run it off the event loop.
    await asyncio.to_thread(_check_public_url_sync, url)


async def _check_request(request: httpx.Request) -> None:
    """httpx hook: runs for the first request and for every redirect hop."""
    await _assert_public_url(str(request.url))


async def scrape_url(url: str) -> dict:
    """
    Fetch `url` and return {"title": str, "text": str}.
    Raises ScrapeError with a user-friendly message on failure.
    """
    headers = {"User-Agent": USER_AGENT}

    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            max_redirects=5,
            headers=headers,
            event_hooks={"request": [_check_request]},
        ) as client:
            async with client.stream("GET", url) as resp:
                if resp.status_code >= 400:
                    raise ScrapeError(f"Page returned an error (HTTP {resp.status_code}).")

                content_type = resp.headers.get("content-type", "")
                if "text/html" not in content_type:
                    raise ScrapeError("That URL doesn't appear to be a webpage (not HTML).")

                body = bytearray()
                async for chunk in resp.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_BYTES:
                        break
                encoding = resp.encoding or "utf-8"
    except httpx.TimeoutException:
        raise ScrapeError("The page took too long to respond.")
    except httpx.TooManyRedirects:
        raise ScrapeError("That link redirects too many times.")
    except httpx.RequestError as e:
        raise ScrapeError(f"Could not reach that URL: {e}")

    html = bytes(body).decode(encoding, errors="replace")
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(NOISE_TAGS):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else url

    # Prefer <article> or <main> if present: usually the actual content,
    # not nav/sidebar/comments noise.
    main = soup.find("article") or soup.find("main") or soup.body or soup

    text = main.get_text(separator=" ", strip=True)
    text = " ".join(text.split())  # collapse whitespace

    if not text:
        raise ScrapeError("No readable text content found on that page.")

    return {"title": title, "text": text[:MAX_CHARS]}
