
import json
from typing import Any, Optional
import redis.asyncio as redis
from _app.core import settings

_r = redis.from_url(settings.redis_cache_url, decode_responses=True)
_prefix = settings.DLQ_KEY_PREFIX

def _key(queue: str) -> str:
    return f"{_prefix}{queue}"

async def enqueue(queue: str, payload: dict[str, Any]) -> None:
    await _r.rpush(_key(queue), json.dumps(payload))

async def dequeue(queue: str) -> Optional[dict[str, Any]]:
    v = await _r.lpop(_key(queue))
    return json.loads(v) if v else None

async def peek(queue: str, start: int = 0, stop: int = -1) -> list[dict[str, Any]]:
    items = await _r.lrange(_key(queue), start, stop)
    return [json.loads(i) for i in items]

async def length(queue: str) -> int:
    return int(await _r.llen(_key(queue)))
