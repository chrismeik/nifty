"""
Step 3 — Transform powerschool.* staging data into core.* Ed-Fi canonical tables.

Reads from the data dict returned by Step 1 (not from Postgres) to avoid a
redundant DB round-trip. Maps PS field shapes to Ed-Fi standard names and
upserts into:
  - core.students
  - core.student_school_associations
  - core.contacts
  - core.student_contact_associations
  - core.student_school_attendance_events

entry_date on student_school_associations is pulled from core.sessions so it
stays stable across daily runs. If no matching session exists for a school,
that school's associations are skipped with a warning.
"""

import logging
from datetime import date, datetime, timezone

from sqlalchemy import text

from _app._postgres import engine

log = logging.getLogger(__name__)

_GRADE_DESCRIPTORS = {
    1:  "First grade",
    2:  "Second grade",
    3:  "Third grade",
    4:  "Fourth grade",
    5:  "Fifth grade",
    6:  "Sixth grade",
    7:  "Seventh grade",
    8:  "Eighth grade",
    9:  "Ninth grade",
    10: "Tenth grade",
    11: "Eleventh grade",
    12: "Twelfth grade",
}


async def transform_to_core(data: dict, target_date: date) -> dict:
    """Transform and upsert all PS data into core.* Ed-Fi tables."""
    async with engine.begin() as conn:
        session_begin_dates = await _get_session_begin_dates(conn, target_date)

        student_count  = await _upsert_core_students(conn, data["students"])
        assoc_count    = await _upsert_student_school_associations(conn, data["students"], session_begin_dates)
        contact_count  = await _upsert_core_contacts(conn, data["contacts"])
        sc_assoc_count = await _upsert_student_contact_associations(conn, data["contacts"])
        event_count    = await _upsert_attendance_events(conn, data["attendance"])

    meta = {
        "students_written":             student_count,
        "school_associations_written":  assoc_count,
        "contacts_written":             contact_count,
        "contact_associations_written": sc_assoc_count,
        "attendance_events_written":    event_count,
    }
    log.info(
        "step3: core — %d students, %d school assocs, %d contacts, %d contact assocs, %d attendance events",
        student_count, assoc_count, contact_count, sc_assoc_count, event_count,
    )
    return meta


# ---------------------------------------------------------------------------
# Session lookup
# ---------------------------------------------------------------------------

async def _get_session_begin_dates(conn, target_date: date) -> dict:
    """Returns {school_id: begin_date} for sessions active on target_date."""
    rows = await conn.execute(
        text("""
            SELECT school_id, begin_date
            FROM core.sessions
            WHERE begin_date <= :d AND end_date >= :d
        """),
        {"d": target_date},
    )
    result = {row.school_id: row.begin_date for row in rows}
    if not result:
        log.warning("step3: no active sessions found for %s — student_school_associations will be skipped", target_date)
    return result


# ---------------------------------------------------------------------------
# core.students
# ---------------------------------------------------------------------------

async def _upsert_core_students(conn, students: list) -> int:
    if not students:
        return 0

    now = datetime.now(timezone.utc)
    sql = text("""
        INSERT INTO core.students (
            student_unique_id, first_name, last_name, middle_name, birth_date,
            created_at, modified_at
        ) VALUES (
            :student_unique_id, :first_name, :last_name, :middle_name, :birth_date,
            :now, :now
        )
        ON CONFLICT (student_unique_id) DO UPDATE SET
            first_name  = EXCLUDED.first_name,
            last_name   = EXCLUDED.last_name,
            middle_name = EXCLUDED.middle_name,
            modified_at = EXCLUDED.modified_at
    """)

    params = [
        {
            "student_unique_id": str(s["ps_student_id"]),
            "first_name":        s["first_name"],
            "last_name":         s["last_name"],
            "middle_name":       s.get("middle_name"),
            "birth_date":        s.get("dob"),
            "now":               now,
        }
        for s in students
    ]
    await conn.execute(sql, params)
    return len(students)


# ---------------------------------------------------------------------------
# core.student_school_associations
# ---------------------------------------------------------------------------

async def _upsert_student_school_associations(conn, students: list, session_begin_dates: dict) -> int:
    if not students or not session_begin_dates:
        return 0

    now = datetime.now(timezone.utc)
    sql = text("""
        INSERT INTO core.student_school_associations (
            student_unique_id, school_id, entry_date,
            entry_grade_level_descriptor, primary_school,
            created_at, modified_at
        ) VALUES (
            :student_unique_id, :school_id, :entry_date,
            :entry_grade_level_descriptor, :primary_school,
            :now, :now
        )
        ON CONFLICT (student_unique_id, school_id, entry_date) DO UPDATE SET
            entry_grade_level_descriptor = EXCLUDED.entry_grade_level_descriptor,
            modified_at                  = EXCLUDED.modified_at
    """)

    params = []
    skipped = 0
    for s in students:
        entry_date = session_begin_dates.get(s["school_id"])
        if not entry_date:
            log.warning(
                "step3: no session for school_id=%s, skipping association for student %s",
                s["school_id"], s["ps_student_id"],
            )
            skipped += 1
            continue
        params.append({
            "student_unique_id":           str(s["ps_student_id"]),
            "school_id":                   s["school_id"],
            "entry_date":                  entry_date,
            "entry_grade_level_descriptor": _GRADE_DESCRIPTORS.get(s.get("grade_level"), "Ungraded"),
            "primary_school":              True,
            "now":                         now,
        })

    if params:
        await conn.execute(sql, params)
    if skipped:
        log.warning("step3: skipped %d student_school_associations due to missing sessions", skipped)

    return len(params)


# ---------------------------------------------------------------------------
# core.contacts
# ---------------------------------------------------------------------------

async def _upsert_core_contacts(conn, contacts: list) -> int:
    if not contacts:
        return 0

    now = datetime.now(timezone.utc)
    sql = text("""
        INSERT INTO core.contacts (
            contact_unique_id, first_name, last_name,
            telephone_number, email_address,
            created_at, modified_at
        ) VALUES (
            :contact_unique_id, :first_name, :last_name,
            :telephone_number, :email_address,
            :now, :now
        )
        ON CONFLICT (contact_unique_id) DO UPDATE SET
            first_name       = EXCLUDED.first_name,
            last_name        = EXCLUDED.last_name,
            telephone_number = EXCLUDED.telephone_number,
            email_address    = EXCLUDED.email_address,
            modified_at      = EXCLUDED.modified_at
    """)

    params = [
        {
            "contact_unique_id": str(c["ps_contact_id"]),
            "first_name":        c["first_name"],
            "last_name":         c["last_name"],
            "telephone_number":  c.get("phone"),
            "email_address":     c.get("email"),
            "now":               now,
        }
        for c in contacts
    ]
    await conn.execute(sql, params)
    return len(contacts)


# ---------------------------------------------------------------------------
# core.student_contact_associations
# ---------------------------------------------------------------------------

async def _upsert_student_contact_associations(conn, contacts: list) -> int:
    if not contacts:
        return 0

    now = datetime.now(timezone.utc)
    sql = text("""
        INSERT INTO core.student_contact_associations (
            student_unique_id, contact_unique_id,
            relation_descriptor, primary_contact_indicator, emergency_contact_status,
            created_at, modified_at
        ) VALUES (
            :student_unique_id, :contact_unique_id,
            :relation_descriptor, :primary_contact_indicator, :emergency_contact_status,
            :now, :now
        )
        ON CONFLICT (student_unique_id, contact_unique_id) DO UPDATE SET
            relation_descriptor       = EXCLUDED.relation_descriptor,
            primary_contact_indicator = EXCLUDED.primary_contact_indicator,
            modified_at               = EXCLUDED.modified_at
    """)

    params = [
        {
            "student_unique_id":        str(c["ps_student_id"]),
            "contact_unique_id":        str(c["ps_contact_id"]),
            "relation_descriptor":      c.get("relationship"),
            "primary_contact_indicator": c.get("priority_order") == 1,
            "emergency_contact_status": False,
            "now":                      now,
        }
        for c in contacts
    ]
    await conn.execute(sql, params)
    return len(contacts)


# ---------------------------------------------------------------------------
# core.student_school_attendance_events
# ---------------------------------------------------------------------------

async def _upsert_attendance_events(conn, attendance: list) -> int:
    if not attendance:
        return 0

    now = datetime.now(timezone.utc)
    sql = text("""
        INSERT INTO core.student_school_attendance_events (
            student_unique_id, school_id, event_date,
            attendance_event_category_descriptor, attendance_event_reason,
            created_at, modified_at
        ) VALUES (
            :student_unique_id, :school_id, :event_date,
            :attendance_event_category_descriptor, :attendance_event_reason,
            :now, :now
        )
        ON CONFLICT (student_unique_id, school_id, event_date, attendance_event_category_descriptor)
        DO UPDATE SET
            attendance_event_reason = EXCLUDED.attendance_event_reason,
            modified_at             = EXCLUDED.modified_at
    """)

    params = [
        {
            "student_unique_id":                    str(a["ps_student_id"]),
            "school_id":                            a["school_id"],
            "event_date":                           date.fromisoformat(a["att_date"]) if isinstance(a["att_date"], str) else a["att_date"],
            "attendance_event_category_descriptor": "Unexcused Absence",
            "attendance_event_reason":              a.get("description"),
            "now":                                  now,
        }
        for a in attendance
    ]
    await conn.execute(sql, params)
    return len(attendance)
