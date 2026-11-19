# app/schemas.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    message_id: UUID
    request_id: Optional[str] = None
    api_key: Optional[str] = None
    idempotency_key: Optional[str] = None
    payload_sha256: str
    payload: dict[str, Any]
    status: str
    error: Optional[str] = None
    enqueued_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
