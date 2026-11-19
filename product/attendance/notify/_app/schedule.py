"""
Nifty daily attendance pipeline schedule.
Fires at 09:00 America/Chicago — queries all active schools and enqueues one task each.
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text

from _app._postgres import engine

log = logging.getLogger(__name__)


async def _enqueue_pipeline_for_all_schools() -> None:
    from notify._app.worker import run_notify_task

    target_date = datetime.now(timezone.utc).date()

    async with engine.connect() as conn:
        rows = await conn.execute(
            text("""
                SELECT DISTINCT school_id
                FROM core.sis_configurations
                WHERE is_active = TRUE
            """)
        )
        school_ids = [row.school_id for row in rows]

    if not school_ids:
        log.warning("scheduler: no active schools found, skipping pipeline run")
        return

    for school_id in school_ids:
        run_notify_task.send(school_id, target_date.isoformat())
        log.info("scheduler: queued pipeline for school=%s date=%s", school_id, target_date)


def register_jobs(scheduler: AsyncIOScheduler) -> None:
    scheduler.add_job(
        _enqueue_pipeline_for_all_schools,
        trigger=CronTrigger(hour=9, minute=0, timezone="America/Chicago"),
        id="nifty_daily_pipeline",
        replace_existing=True,
    )
