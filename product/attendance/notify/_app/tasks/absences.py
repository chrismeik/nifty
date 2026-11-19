# <product id="aeec5b50-72b5-461d-a2a1-0acfcbe2be97">
"""
Step 4 — Identify today's unexcused absences from core.* canonical tables.

Queries core.student_school_attendance_events for the target school and date,
filtered to unexcused absences only. Returns the list of student_unique_ids
that feed Steps 5 (analytics) and 7 (contact lookup).
"""

import logging
from datetime import date

from sqlalchemy import text

from _app._postgres import engine

log = logging.getLogger(__name__)

_UNEXCUSED = "Unexcused Absence"


async def get_unexcused_absences(school_id: int, target_date: date) -> tuple[list[str], dict]:
    """
    Returns (student_ids, meta) where student_ids is a list of student_unique_id
    strings for students with an unexcused absence at the given school on target_date.
    """
    async with engine.connect() as conn:
        rows = await conn.execute(
            text("""
                SELECT e.student_unique_id
                FROM core.student_school_attendance_events e
                JOIN core.student_school_associations a
                  ON a.student_unique_id = e.student_unique_id
                 AND a.school_id = e.school_id
                 AND a.exit_withdraw_date IS NULL
                WHERE e.school_id  = :school_id
                  AND e.event_date = :target_date
                  AND e.attendance_event_category_descriptor = :category
                ORDER BY e.student_unique_id
            """),
            {"school_id": school_id, "target_date": target_date, "category": _UNEXCUSED},
        )
        student_ids = [row.student_unique_id for row in rows]

    meta = {
        "school_id":    school_id,
        "absent_count": len(student_ids),
        "student_ids":  student_ids,
    }
    log.info("step4: %d unexcused absences for school=%s on %s", len(student_ids), school_id, target_date)
    return student_ids, meta
# </product>
