
from fastapi import Header, HTTPException, Response
from _app._fastapi.rate_limit import allow

async def rate_limiter(
    response: Response,
    x_client_id: str | None = Header(default=None),
    window_sec: int = 60,
    max_hits: int = 120,
) -> None:
    client = x_client_id or "anonymous"
    ok, remaining = await allow(client, window_sec=window_sec, max_hits=max_hits)
    response.headers["X-RateLimit-Limit"] = str(max_hits)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Window"] = str(window_sec)
    if not ok:
        raise HTTPException(status_code=429, detail="Too Many Requests")
