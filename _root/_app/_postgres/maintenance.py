# app/maintenance.py
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete

from .settings import get_settings
from .db import get_session
from .models import IngestEvent

log = logging.getLogger(__name__)

async def prune_ingest_events(days: int | None = None, batch_size: int = 1000, dry_run: bool = False) -> int:
    """Delete ingest_events older than N days in batches. Returns rows deleted."""
    cutoff_days = days or get_settings().RETENTION_DAYS
    cutoff = datetime.now(timezone.utc) - timedelta(days=cutoff_days)

    total = 0
    async for session in get_session():
        while True:
            ids = (
                (await session.execute(
                    select(IngestEvent.message_id)
                    .where(IngestEvent.enqueued_at < cutoff)
                    .limit(batch_size)
                ))
                .scalars()
                .all()
            )
            if not ids:
                break

            if dry_run:
                total += len(ids)
                break

            await session.execute(delete(IngestEvent).where(IngestEvent.message_id.in_(ids)))
            await session.commit()
            total += len(ids)
            log.info("pruned %s rows older than %s", len(ids), cutoff.isoformat())

        await session.close()

    log.info("prune complete: deleted=%s (cutoff_days=%s)", total, cutoff_days)
    return total
