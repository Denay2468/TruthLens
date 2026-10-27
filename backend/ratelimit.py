"""
Very small in-memory rate limiter (per client IP, sliding window).

Protects the free-tier API quota (NFR-2). It is per-process and resets on
restart, which is fine for a single-instance demo. If the app is deployed
behind a proxy, every request may appear to come from the proxy's IP; in
that case switch to a shared store or the platform's own rate limiting.
"""

import os
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

WINDOW_SECONDS = 60
_hits: dict = defaultdict(deque)


def rate_limit(request: Request) -> None:
    """FastAPI dependency: raises HTTP 429 when a client sends too many requests."""
    limit = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "20"))
    if limit <= 0:  # 0 disables the limiter
        return

    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    window = _hits[client_ip]

    while window and now - window[0] > WINDOW_SECONDS:
        window.popleft()

    if len(window) >= limit:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a minute and try again.",
        )
    window.append(now)


def reset() -> None:
    """Clear all counters (used by tests)."""
    _hits.clear()
