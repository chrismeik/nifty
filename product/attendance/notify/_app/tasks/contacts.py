# <product id="5cc31138-1449-457e-bda0-83d8c0063fbd">
"""
Step 6 — Pull primary contact data for absent students.

Queries core.contacts and core.student_contact_associations to get the primary
guardian's phone number for each absent student. Students with no primary
contact or no phone number on file are tracked in meta but not returned —
they will be logged as skipped in Step 7.
"""

import logging
from datetime import date

from sqlalchemy import text

from _app._postgres import engine

log = logging.getLogger(__name__)


async def get_contacts_for_students(
    student_ids: list[str], school_id: int, target_date: date
) -> tuple[list[dict], dict]:
    """
    Returns (contacts, meta) where contacts is a list of dicts:
        {
            student_unique_id: str,
            contact_unique_id: str,
            first_name:        str,
            last_name:         str,
            phone:             str,
        }

    Only primary contacts with a phone number are included.
    """
    if not student_ids:
        meta = {"school_id": school_id, "contacts_found": 0, "no_contact": 0, "no_phone": 0}
        return [], meta

    async with engine.connect() as conn:
        rows = await conn.execute(
            text("""
                SELECT
                    a.student_unique_id,
                    c.contact_unique_id,
                    c.first_name,
                    c.last_name,
                    c.telephone_number AS phone
                FROM core.student_contact_associations a
                JOIN core.contacts c
                  ON c.contact_unique_id = a.contact_unique_id
                WHERE a.student_unique_id  = ANY(:student_ids)
                  AND a.primary_contact_indicator = TRUE
                ORDER BY a.student_unique_id
            """),
            {"student_ids": student_ids},
        )
        all_rows = rows.fetchall()

    contacted_student_ids = {row.student_unique_id for row in all_rows}
    no_contact = [sid for sid in student_ids if sid not in contacted_student_ids]

    contacts_with_phone = [row._asdict() for row in all_rows if row.phone]
    no_phone = [row.student_unique_id for row in all_rows if not row.phone]

    meta = {
        "school_id":      school_id,
        "contacts_found": len(contacts_with_phone),
        "no_contact":     len(no_contact),
        "no_phone":       len(no_phone),
    }

    if no_contact:
        log.warning("step6: %d students have no primary contact on file: %s", len(no_contact), no_contact)
    if no_phone:
        log.warning("step6: %d students have a contact but no phone number: %s", len(no_phone), no_phone)

    log.info(
        "step6: %d contacts found, %d no contact, %d no phone",
        len(contacts_with_phone), len(no_contact), len(no_phone),
    )
    return contacts_with_phone, meta
# </product>
