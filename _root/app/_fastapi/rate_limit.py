
# import time
from typing import Tuple
import redis.asyncio as redis
from _app.core import settings

_r = redis.from_url(settings.redis_cache_url, decode_responses=True)
_prefix = settings.RATE_LIMIT_PREFIX

def _key(client_id: str, window_sec: int) -> str:
    return f"{_prefix}{client_id}:{window_sec}"

async def allow(client_id: str, window_sec: int, max_hits: int) -> Tuple[bool, int]:
    # now = int(time.time())
    k = _key(client_id, window_sec)
    pipe = _r.pipeline()
    pipe.incr(k, amount=1)
    pipe.expire(k, window_sec)
    count, _ = await pipe.execute()
    remaining = max(0, max_hits - int(count))
    return (int(count) <= max_hits, remaining)
