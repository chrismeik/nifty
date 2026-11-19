from __future__ import annotations

import json
import uuid
from typing import Any

from redis import asyncio as aioredis
from sqlalchemy import func, select, update

from _app._postgres.db import SessionLocal
from _app._postgres.models import IngestEvent
from _app._dramatiq.settings import get_settings
from _app._dramatiq.job_metrics import INGEST_DLQ_TOTAL


async def fetch_payload(message_id: uuid.UUID) -> str | None:
    """Return the stored payload for a message_id."""
    async with SessionLocal() as session:
        res = await session.execute(
            select(IngestEvent.payload).where(IngestEvent.message_id == message_id)
        )
        return res.scalar_one_or_none()


async def set_status(
    message_id: uuid.UUID, status: str, error: str | None = None
) -> None:
    """Update IngestEvent status and timestamps."""
    async with SessionLocal() as session:
        values: dict[str, Any] = {"status": status}
        if status == "processing":
            values["started_at"] = func.now()
        if status in ("done", "error"):
            values["finished_at"] = func.now()
        if error is not None:
            values["error"] = error
        await session.execute(
            update(IngestEvent)
            .where(IngestEvent.message_id == message_id)
            .values(**values)
        )
        await session.commit()


async def push_dlq(message_id: str, headers: dict, error: str) -> None:
    """Push a failed job record to the Redis DLQ."""
    settings = get_settings()
    client = aioredis.from_url(
        settings.redis_cache_url, encoding="utf-8", decode_responses=True
    )
    key = f"{settings.DLQ_KEY_PREFIX}default"
    try:
        try:
            mi = uuid.UUID(message_id)
        except Exception:
            mi = uuid.uuid4()
        payload = await fetch_payload(mi)
        rec = {
            "message_id": message_id,
            "payload": payload,
            "headers": headers or {},
            "error": error,
            "ts": int(__import__("time").time()),
        }
        await client.lpush(key, json.dumps(rec))
        INGEST_DLQ_TOTAL.inc()
    finally:
        await client.close()