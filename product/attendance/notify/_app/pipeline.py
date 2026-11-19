"""
Nifty attendance notification pipeline orchestrator.

Runs all steps in sequence for a given school and date. The SIS adapter is
looked up dynamically from core.sis_configurations so the pipeline is agnostic
to which SIS a school uses.

Idempotency: if a completed job already exists for this school and date, the
pipeline exits immediately without re-running any steps.
"""

import logging
from datetime import date

from sqlalchemy import text

from _app._postgres import engine
from _app._jobs import check_already_done, create_job, update_job_step, complete_job, fail_job
from notify._app.tasks.sources.adapters.registry import get_adapter
from notify._app.tasks.absences import get_unexcused_absences
from notify._app.tasks.analytics import update_absence_summary
from notify._app.tasks.contacts import get_contacts_for_students
from notify._app.tasks.notifications import send_notifications

log = logging.getLogger(__name__)

_PRODUCT  = "nifty"
_JOB_TYPE = "attendance_pipeline"


async def run_attendance_pipeline(school_id: int, target_date: date) -> None:
    """Entry point called by the Dramatiq worker."""
    scope = str(school_id)

    if await check_already_done(_PRODUCT, _JOB_TYPE, target_date, scope=scope):
        return

    sis_type, config = await _get_sis_config(school_id)
    adapter = get_adapter(sis_type, config)

    job_id = await create_job(_PRODUCT, _JOB_TYPE, target_date, scope=scope)

    try:
        # Step 1 — Pull from SIS (or load from parquet cache)
        data, meta = adapter.fetch(school_id, target_date)
        await update_job_step(job_id, "step1_pull", meta)

        # Step 2 — Upsert into SIS-specific staging tables
        meta = await adapter.stage(data)
        await update_job_step(job_id, "step2_stage", meta)

        # Step 3 — Transform into core.* Ed-Fi canonical tables
        meta = await adapter.transform(data, target_date)
        await update_job_step(job_id, "step3_transform", meta)

        # Step 4 — Identify unexcused absences for today
        absent_student_ids, meta = await get_unexcused_absences(school_id, target_date)
        await update_job_step(job_id, "step4_absences", meta)

        # Step 5 — Update YTD absence counts in analytics
        absent_student_ids, meta = await update_absence_summary(absent_student_ids, school_id, target_date)
        await update_job_step(job_id, "step5_analytics", meta)

        # Step 6 — Pull primary contact data for absent students
        contacts, meta = await get_contacts_for_students(absent_student_ids, school_id, target_date)
        await update_job_step(job_id, "step6_contacts", meta)

        # Step 7 — Merge contacts, send texts, log outcomes
        results, meta = await send_notifications(absent_student_ids, contacts, job_id, school_id, target_date)
        await update_job_step(job_id, "step7_notify", meta)

        await complete_job(job_id)

    except Exception as exc:
        log.exception("attendance pipeline failed for school=%s on %s", school_id, target_date)
        await fail_job(job_id, str(exc))
        raise


async def _get_sis_config(school_id: int) -> tuple[str, dict]:
    """Look up the active SIS type and connection config for a school."""
    async with engine.connect() as conn:
        row = await conn.execute(
            text("""
                SELECT sis_type, connection_config
                FROM core.sis_configurations
                WHERE school_id = :school_id
                  AND is_active = TRUE
                LIMIT 1
            """),
            {"school_id": school_id},
        )
        result = row.fetchone()

    if not result:
        raise ValueError(f"No active SIS configuration found for school_id={school_id}")

    return result.sis_type, result.connection_config
