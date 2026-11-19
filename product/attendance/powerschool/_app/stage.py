"""
Step 2 — Upsert raw PowerSchool data into powerschool.* staging tables.

Accepts the data dict returned by Step 1 and writes it into:
  - powerschool.students
  - powerschool.attendance
  - powerschool.contacts

All three are upserts (ON CONFLICT DO UPDATE) so re-running on the same day
updates existing rows rather than duplicating them.
"""

import logging
from datetime import date, datetime, timezone

from sqlalchemy import text

from _app._postgres import engine

log = logging.getLogger(__name__)


async def stage_to_postgres(data: dict) -> dict:
    """Write students, attendance, and contacts into powerschool.* staging tables."""
    async with engine.begin() as conn:
        student_count    = await _upsert_students(conn, data["students"])
        attendance_count = await _upsert_attendance(conn, data["attendance"])
        contact_count    = await _upsert_contacts(conn, data["contacts"])

    meta = {
        "students_staged":   student_count,
        "attendance_staged": attendance_count,
        "contacts_staged":   contact_count,
    }
    log.info("step2: staged %d students, %d attendance records, %d contacts", student_count, attendance_count, contact_count)
    return meta


async def _upsert_students(conn, students: list) -> int:
    if not students:
        return 0

    sql = text("""
        INSERT INTO powerschool.students (
            ps_student_id, student_number, first_name, last_name,
            grade_level, school_id, ingested_at
        ) VALUES (
            :ps_student_id, :student_number, :first_name, :last_name,
            :grade_level, :school_id, :ingested_at
        )
        ON CONFLICT (ps_student_id) DO UPDATE SET
            student_number = EXCLUDED.student_number,
            first_name     = EXCLUDED.first_name,
            last_name      = EXCLUDED.last_name,
            grade_level    = EXCLUDED.grade_level,
            school_id      = EXCLUDED.school_id,
            ingested_at    = EXCLUDED.ingested_at
    """)

    now = datetime.now(timezone.utc)
    await conn.execute(sql, [{**s, "ingested_at": now} for s in students])
    return len(students)


async def _upsert_attendance(conn, attendance: list) -> int:
    if not attendance:
        return 0

    sql = text("""
        INSERT INTO powerschool.attendance (
            ps_attendance_id, ps_student_id, school_id,
            att_date, att_code, description, ingested_at
        ) VALUES (
            :ps_attendance_id, :ps_student_id, :school_id,
            :att_date, :att_code, :description, :ingested_at
        )
        ON CONFLICT (ps_attendance_id) DO UPDATE SET
            ps_student_id = EXCLUDED.ps_student_id,
            school_id     = EXCLUDED.school_id,
            att_date      = EXCLUDED.att_date,
            att_code      = EXCLUDED.att_code,
            description   = EXCLUDED.description,
            ingested_at   = EXCLUDED.ingested_at
    """)

    now = datetime.now(timezone.utc)
    await conn.execute(sql, [{**a, "att_date": date.fromisoformat(a["att_date"]) if isinstance(a["att_date"], str) else a["att_date"], "ingested_at": now} for a in attendance])
    return len(attendance)


async def _upsert_contacts(conn, contacts: list) -> int:
    if not contacts:
        return 0

    sql = text("""
        INSERT INTO powerschool.contacts (
            ps_contact_id, ps_student_id, first_name, last_name,
            relationship, priority_order, phone, email, ingested_at
        ) VALUES (
            :ps_contact_id, :ps_student_id, :first_name, :last_name,
            :relationship, :priority_order, :phone, :email, :ingested_at
        )
        ON CONFLICT (ps_contact_id) DO UPDATE SET
            ps_student_id  = EXCLUDED.ps_student_id,
            first_name     = EXCLUDED.first_name,
            last_name      = EXCLUDED.last_name,
            relationship   = EXCLUDED.relationship,
            priority_order = EXCLUDED.priority_order,
            phone          = EXCLUDED.phone,
            email          = EXCLUDED.email,
            ingested_at    = EXCLUDED.ingested_at
    """)

    now = datetime.now(timezone.utc)
    await conn.execute(sql, [{**c, "ingested_at": now} for c in contacts])
    return len(contacts)
