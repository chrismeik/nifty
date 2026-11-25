"""
Platform-level job management utility.

The pipeline calls these functions to track a long-running job in platform.jobs.
Metadata is a JSONB field updated after each step — new step keys are merged in
rather than replacing the whole object, so the full run history accumulates.

scope is an optional string that narrows idempotency within a product/job_type/date.
Example: str(school_id) for per-school-per-day jobs.

Usage:
    job_id = await create_job("myproduct", "daily_pipeline", target_date, scope="42")
    await update_job_step(job_id, "step1_pull", {"source": "api", "count": 4})
    await update_job_step(job_id, "step2_stage", {"rows_staged": 4})
    await complete_job(job_id)
    # on any exception:
    await fail_job(job_id, str(exc))
"""

import json
import logging
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import text

from _app._postgres.db import engine

log = logging.getLogger(__name__)


async def check_already_done(
    product: str, job_type: str, target_date: date, scope: str | None = None
) -> bool:
    """Return True if a completed job already exists for this product/type/date/scope."""
    async with engine.connect() as conn:
        row = await conn.execute(
            text("""
                SELECT id FROM platform.jobs
                WHERE product     = :product
                  AND job_type    = :job_type
                  AND target_date = :target_date
                  AND COALESCE(scope, '') = COALESCE(:scope, '')
                  AND status      = 'done'
                LIMIT 1
            """),
            {"product": product, "job_type": job_type, "target_date": target_date, "scope": scope},
        )
        result = row.fetchone()

    if result:
        log.info("job already done for %s/%s scope=%s on %s — skipping", product, job_type, scope, target_date)
        return True
    return False


async def create_job(
    product: str, job_type: str, target_date: date, scope: str | None = None
) -> UUID:
    """Insert a new job row with status 'running' and return its id."""
    now = datetime.now(timezone.utc)
    async with engine.begin() as conn:
        row = await conn.execute(
            text("""
                INSERT INTO platform.jobs
                    (product, job_type, target_date, scope, status, started_at, metadata)
                VALUES
                    (:product, :job_type, :target_date, :scope, 'running', :now, '{}')
                RETURNING id
            """),
            {"product": product, "job_type": job_type, "target_date": target_date, "scope": scope, "now": now},
        )
        job_id = row.scalar_one()

    log.info("job started: %s %s/%s scope=%s on %s", job_id, product, job_type, scope, target_date)
    return job_id


async def update_job_step(job_id: UUID, step: str, data: dict) -> None:
    """
    Merge a step's result into the metadata JSONB field.

    Each call adds one key without touching existing keys:
        metadata = metadata || '{"step1_pull": {"completed_at": "...", ...}}'
    """
    now = datetime.now(timezone.utc)
    payload = {step: {"completed_at": now.isoformat(), **data}}

    async with engine.begin() as conn:
        await conn.execute(
            text("""
                UPDATE platform.jobs
                SET metadata = metadata || CAST(:payload AS jsonb)
                WHERE id = :job_id
            """),
            {"job_id": str(job_id), "payload": json.dumps(payload)},
        )

    log.info("job %s — %s complete: %s", job_id, step, data)


async def complete_job(job_id: UUID) -> None:
    """Mark the job as done."""
    now = datetime.now(timezone.utc)
    async with engine.begin() as conn:
        await conn.execute(
            text("""
                UPDATE platform.jobs
                SET status = 'done', finished_at = :now
                WHERE id = :job_id
            """),
            {"job_id": str(job_id), "now": now},
        )
    log.info("job %s — done", job_id)


async def fail_job(job_id: UUID, error: str) -> None:
    """Mark the job as failed and record the error message."""
    now = datetime.now(timezone.utc)
    async with engine.begin() as conn:
        await conn.execute(
            text("""
                UPDATE platform.jobs
                SET status = 'failed', finished_at = :now, error = :error
                WHERE id = :job_id
            """),
            {"job_id": str(job_id), "now": now, "error": error},
        )
    log.error("job %s — failed: %s", job_id, error)
