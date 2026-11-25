import hashlib
import json
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import IngestEvent

def payload_sha256(payload) -> str:
    # Stable JSON encode
    data = json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()

async def get_by_idempotency(session: AsyncSession, api_key: Optional[str], idem_key: str) -> Optional[IngestEvent]:
    stmt = select(IngestEvent).where(
        IngestEvent.api_key == api_key,
        IngestEvent.idempotency_key == idem_key,
    )
    res = await session.execute(stmt)
    return res.scalar_one_or_none()
