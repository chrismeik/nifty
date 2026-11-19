"""
Dramatiq actor for the nifty attendance pipeline.
Enqueued by the HTTP trigger endpoint or the APScheduler daily job.
"""

import asyncio
import logging
from datetime import date

import dramatiq

from _app._dramatiq import redis_broker  # noqa: F401 — registers the Dramatiq broker

log = logging.getLogger(__name__)


@dramatiq.actor(queue_name="default")
def run_notify_task(school_id: int, target_date_iso: str) -> None:
    from _app._postgres import engine
    from notify._app.pipeline import run_attendance_pipeline

    target_date = date.fromisoformat(target_date_iso)
    log.info("nifty pipeline starting: school=%s date=%s", school_id, target_date)

    async def _run():
        # Dispose existing connections — they're bound to a different event loop
        await engine.dispose()
        await run_attendance_pipeline(school_id, target_date)

    asyncio.run(_run())
    log.info("nifty pipeline complete: school=%s date=%s", school_id, target_date)
