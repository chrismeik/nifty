# <product id="2a75e0e9-f81e-4799-8f8b-02e2a497b734">
"""
Step 7 — Send absence notifications and log results.

Merges absent student IDs with contact data, POSTs to /dialmycalls/texts/send
for each contact, and writes every outcome to analytics.notification_log.
"""

import os
import logging
import uuid
from datetime import date

import httpx
from sqlalchemy import text

from _app._postgres import engine

log = logging.getLogger(__name__)


def _api_base() -> str:
    return os.getenv("INTERNAL_API_URL", "http://localhost:8000")


def _build_message(first_name: str, last_name: str, event_date: date) -> str:
    d = event_date.strftime("%-m/%-d/%y")
    return (
        f"Unexcused Absence (UA): {d} — {first_name} {last_name}. "
        f"Please contact the school office to resolve."
    )


async def send_notifications(
    absent_student_ids: list[str],
    contacts: list[dict],
    job_id: uuid.UUID,
    school_id: int,
    target_date: date,
) -> tuple[dict, dict]:
    """
    Returns (results, meta).

    results is a list of per-student outcome dicts:
        { student_unique_id, status, broadcast_id, error_message }
    meta summarises counts: sent, skipped, failed.
    """
    if not absent_student_ids:
        meta = {"school_id": school_id, "sent": 0, "skipped": 0, "failed": 0}
        return [], meta

    contact_by_student = {c["student_unique_id"]: c for c in contacts}

    send_list = []
    skip_list = []

    for sid in absent_student_ids:
        contact = contact_by_student.get(sid)
        if contact:
            send_list.append(contact)
        else:
            skip_list.append(sid)

    log.info(
        "step7: %d to send, %d skipped for school=%s",
        len(send_list), len(skip_list), school_id,
    )

    results = []
    async with httpx.AsyncClient() as client:
        for contact in send_list:
            msg = _build_message(
                contact["first_name"], contact["last_name"], target_date
            )
            try:
                resp = await client.post(
                    f"{_api_base()}/dialmycalls/texts/send",
                    json={"to": contact["phone"], "message": msg},
                    timeout=30.0,
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    results.append({
                        "student_unique_id": contact["student_unique_id"],
                        "contact_unique_id": contact["contact_unique_id"],
                        "phone_number":      contact["phone"],
                        "status":            "sent",
                        "broadcast_id":      data.get("broadcast_id", ""),
                        "error_message":     None,
                    })
                else:
                    results.append({
                        "student_unique_id": contact["student_unique_id"],
                        "contact_unique_id": contact["contact_unique_id"],
                        "phone_number":      contact["phone"],
                        "status":            "failed",
                        "broadcast_id":      None,
                        "error_message":     resp.text[:500],
                    })
            except Exception as exc:
                results.append({
                    "student_unique_id": contact["student_unique_id"],
                    "contact_unique_id": contact["contact_unique_id"],
                    "phone_number":      contact["phone"],
                    "status":            "failed",
                    "broadcast_id":      None,
                    "error_message":     str(exc)[:500],
                })

    for sid in skip_list:
        results.append({
            "student_unique_id": sid,
            "contact_unique_id": None,
            "phone_number":      None,
            "status":            "skipped",
            "broadcast_id":      None,
            "error_message":     None,
        })

    sent_count    = sum(1 for r in results if r["status"] == "sent")
    failed_count  = sum(1 for r in results if r["status"] == "failed")
    skipped_count = sum(1 for r in results if r["status"] == "skipped")

    log.info(
        "step7: sent=%d failed=%d skipped=%d for school=%s",
        sent_count, failed_count, skipped_count, school_id,
    )

    await _log_results(results, job_id, target_date)

    meta = {
        "school_id": school_id,
        "sent":      sent_count,
        "failed":    failed_count,
        "skipped":   skipped_count,
        "texts": [
            {
                "student_unique_id": r["student_unique_id"],
                "status":            r["status"],
                "broadcast_id":      r["broadcast_id"],
                "error_message":     r["error_message"],
            }
            for r in results
        ],
    }
    return results, meta


async def _log_results(
    results: list[dict],
    job_id: uuid.UUID,
    target_date: date,
) -> None:
    if not results:
        return

    params = [
        {
            "job_id":            str(job_id),
            "student_unique_id": r["student_unique_id"],
            "contact_unique_id": r["contact_unique_id"],
            "phone_number":      r["phone_number"],
            "event_date":        target_date,
            "status":            r["status"],
            "broadcast_id":      r["broadcast_id"],
            "error_message":     r["error_message"],
        }
        for r in results
    ]

    async with engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO analytics.notification_log
                    (job_id, student_unique_id, contact_unique_id,
                     phone_number, event_date, status, broadcast_id, error_message)
                VALUES
                    (:job_id, :student_unique_id, :contact_unique_id,
                     :phone_number, :event_date, :status, :broadcast_id, :error_message)
            """),
            params,
        )

    log.info("step7: logged %d notification outcomes", len(results))
# </product>
