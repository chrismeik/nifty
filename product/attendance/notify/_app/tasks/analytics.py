# <product id="3bf17e70-0056-4523-89ca-5db6bb92d639">
"""
Step 5 — Update analytics.student_absence_summary with today's unexcused absences.

Increments the YTD absence count for each absent student within the active
academic session. The DO UPDATE WHERE clause guards against double-counting if
the pipeline runs more than once on the same day.
"""

import logging
from datetime import date

from sqlalchemy import text

from _app._postgres import engine

log = logging.getLogger(__name__)


async def update_absence_summary(
    student_ids: list[str], school_id: int, target_date: date
) -> tuple[list[str], dict]:
    """
    Increments total_absences for each student in student_ids.

    Returns (processed_ids, meta) where processed_ids are the students whose
    counts were actually incremented (skips any already updated today).
    """
    if not student_ids:
        meta = {"school_id": school_id, "updated_count": 0, "skipped_count": 0}
        log.info("step5: no absent students to process for school=%s", school_id)
        return [], meta

    session = await _get_active_session(school_id, target_date)
    if not session:
        raise ValueError(f"No active session found for school_id={school_id} on {target_date}")

    session_name, school_year = session

    sql = text("""
        INSERT INTO analytics.student_absence_summary
            (student_unique_id, school_id, session_name, school_year, total_absences, last_updated)
        VALUES
            (:student_unique_id, :school_id, :session_name, :school_year, 1, NOW())
        ON CONFLICT (student_unique_id, school_id, session_name, school_year) DO UPDATE SET
            total_absences = analytics.student_absence_summary.total_absences + 1,
            last_updated   = NOW()
        WHERE
            analytics.student_absence_summary.last_updated::date < :target_date
        RETURNING student_unique_id
    """)

    processed_ids = []
    async with engine.begin() as conn:
        for sid in student_ids:
            row = await conn.execute(sql, {
                "student_unique_id": sid,
                "school_id":         school_id,
                "session_name":      session_name,
                "school_year":       school_year,
                "target_date":       target_date,
            })
            result = row.fetchone()
            if result:
                processed_ids.append(result.student_unique_id)

    skipped_count = len(student_ids) - len(processed_ids)

    meta = {
        "school_id":     school_id,
        "updated_count": len(processed_ids),
        "skipped_count": skipped_count,
        "session_name":  session_name,
        "school_year":   school_year,
    }

    if skipped_count:
        log.warning("step5: %d students already updated today — skipped", skipped_count)

    log.info(
        "step5: updated absence summary for %d students, skipped %d",
        len(processed_ids), skipped_count,
    )
    return processed_ids, meta


async def _get_active_session(school_id: int, target_date: date) -> tuple[str, int] | None:
    """Return (session_name, school_year) for the active session on target_date."""
    async with engine.connect() as conn:
        row = await conn.execute(
            text("""
                SELECT session_name, school_year
                FROM core.sessions
                WHERE school_id  = :school_id
                  AND begin_date <= :d
                  AND end_date   >= :d
                LIMIT 1
            """),
            {"school_id": school_id, "d": target_date},
        )
        result = row.fetchone()

    return (result.session_name, result.school_year) if result else None
# </product>
