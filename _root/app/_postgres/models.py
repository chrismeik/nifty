import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Enum, Index, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

JOB_STATUS = ("queued", "processing", "done", "error")

class IngestEvent(Base):
    __tablename__ = "ingest_events"

    __table_args__ = (
        Index(
            "uq_ingest_api_key_idempotency",
            "api_key",
            "idempotency_key",
            unique=True,
            postgresql_where=text("idempotency_key IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False)
    request_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    api_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    payload_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="")

    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    status: Mapped[str] = mapped_column(Enum(*JOB_STATUS, name="job_status"), nullable=False, default="queued")
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    enqueued_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

Index("idx_ingest_events_enqueued_at", IngestEvent.enqueued_at.desc())
Index("idx_ingest_events_status_enqueued_at", IngestEvent.status, IngestEvent.enqueued_at.desc())
# Unique idempotency per api_key when idempotency_key is not null
Index(
    "uq_ingest_events_api_key_idem",
    IngestEvent.api_key, IngestEvent.idempotency_key,
    unique=True,
    postgresql_where=text("idempotency_key IS NOT NULL")
)
