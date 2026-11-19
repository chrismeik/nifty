# <product id="c5d18042-39b2-4787-8ac5-dd44f9a9a707">
import os
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, HTTPException, Body, Response
from pydantic import BaseModel

from sqlalchemy import text
from _app._postgres import engine

log = logging.getLogger(__name__)

router = APIRouter()


_LEADS_DIR  = Path("/root-product/marketing/_data/_postgres/nifty/marketing/leads")
_RAFFLE_DIR = Path("/root-product/marketing/_data/_postgres/nifty/marketing/raffle")


class LeadRequest(BaseModel):
    name: str
    phone_number: str
    district_name: str
    email: str | None = None
    source: str | None = None
    sis_name: str | None = None
    demo_availability: str | None = None
    student_count: int | None = None


class LeadResponse(BaseModel):
    id: uuid.UUID
    name: str
    phone_number: str
    district_name: str
    email: str | None
    source: str | None
    sis_name: str | None
    demo_availability: str | None
    student_count: int | None
    created_at: datetime


class AllLeadsResponse(BaseModel):
    id: uuid.UUID
    name: str
    phone_number: str
    district_name: str
    email: str | None
    source: str | None
    sis_name: str | None
    demo_availability: str | None
    student_count: int | None
    created_at: datetime
    raffle_id: uuid.UUID | None = None
    raffle_group: int | None = None
    raffle_location: str | None = None


_S3_BUCKET = "niftyedtools.com-data"
_DATA_ROOT  = Path("/root-product/marketing/_data/_postgres/nifty")


def _s3():
    import boto3
    return boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )


def _partition_dir(base: Path, dt: datetime) -> Path:
    d = base / f"year={dt.year}" / f"month={dt.month:02d}" / f"day={dt.day:02d}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _save_parquet(local_path: Path, df: pd.DataFrame) -> None:
    df.to_parquet(local_path, index=False)
    try:
        s3_key = str(local_path.relative_to(_DATA_ROOT))
        _s3().upload_file(str(local_path), _S3_BUCKET, s3_key)
    except Exception:
        log.exception("s3 upload failed for %s", local_path)


def _save_lead_parquet(lead_id: uuid.UUID, result) -> None:
    row = {
        "id":                str(lead_id),
        "name":              result.name,
        "phone_number":      result.phone_number,
        "district_name":     result.district_name,
        "email":             result.email,
        "source":            result.source,
        "sis_name":          result.sis_name,
        "demo_availability": result.demo_availability,
        "student_count":     result.student_count,
        "created_at":        result.created_at,
    }
    path = _partition_dir(_LEADS_DIR, result.created_at) / f"{lead_id}.parquet"
    _save_parquet(path, pd.DataFrame([row]))


def _save_raffle_parquet(raffle_id: uuid.UUID, result) -> None:
    row = {
        "id":              str(raffle_id),
        "lead_id":         str(result.lead_id),
        "raffle_location": result.raffle_location,
        "raffle_group":    result.raffle_group,
        "created_at":      result.created_at,
    }
    path = _partition_dir(_RAFFLE_DIR, result.created_at) / f"{raffle_id}.parquet"
    _save_parquet(path, pd.DataFrame([row]))


@router.get("", response_model=list[AllLeadsResponse])
async def list_leads() -> list[AllLeadsResponse]:
    async with engine.begin() as conn:
        rows = await conn.execute(
            text("""
                SELECT l.id, l.name, l.phone_number, l.district_name, l.email, l.source, l.sis_name,
                       l.demo_availability, l.student_count, l.created_at,
                       r.id AS raffle_id, r.raffle_group, r.raffle_location
                FROM marketing.leads l
                LEFT JOIN marketing.raffle r ON r.lead_id = l.id
                ORDER BY l.created_at DESC
            """)
        )
        return [AllLeadsResponse(**row._asdict()) for row in rows.fetchall()]


@router.post("", response_model=LeadResponse, status_code=201)
async def create_lead(request: LeadRequest, background_tasks: BackgroundTasks, response: Response) -> LeadResponse:
    if request.source == "raffle":
        async with engine.begin() as conn:
            dupe = await conn.execute(
                text("""
                    SELECT id, name, phone_number, district_name, email, source, sis_name, demo_availability, created_at
                    FROM marketing.leads
                    WHERE source = 'raffle'
                      AND phone_number = :phone
                      AND COALESCE(email, '') = COALESCE(:email, '')
                """),
                {"phone": request.phone_number, "email": request.email},
            )
            existing = dupe.fetchone()
        if existing:
            log.info("duplicate raffle entry ignored: %s", request.phone_number)
            if existing.email:
                background_tasks.add_task(_send_raffle_email, existing.email, existing.name)
            response.status_code = 200
            return LeadResponse(**existing._asdict())

    lead_id = uuid.uuid4()
    async with engine.begin() as conn:
        row = await conn.execute(
            text("""
                INSERT INTO marketing.leads (id, name, phone_number, district_name, email, source, sis_name, demo_availability, student_count)
                VALUES (:id, :name, :phone_number, :district_name, :email, :source, :sis_name, :demo_availability, :student_count)
                RETURNING id, name, phone_number, district_name, email, source, sis_name, demo_availability, student_count, created_at
            """),
            {
                "id":                lead_id,
                "name":              request.name,
                "phone_number":      request.phone_number,
                "district_name":     request.district_name,
                "email":             request.email,
                "source":            request.source,
                "sis_name":          request.sis_name,
                "demo_availability": request.demo_availability,
                "student_count":     request.student_count,
            },
        )
        result = row.fetchone()

    _save_lead_parquet(lead_id, result)
    log.info("lead captured: %s — %s", result.name, result.district_name)

    if request.source == "raffle":
        async with engine.begin() as conn:
            raffle_row = await conn.execute(
                text("INSERT INTO marketing.raffle (lead_id) VALUES (:lead_id) RETURNING id, lead_id, raffle_location, raffle_group, created_at"),
                {"lead_id": lead_id},
            )
            raffle_result = raffle_row.fetchone()
        _save_raffle_parquet(raffle_result.id, raffle_result)
        if request.email:
            background_tasks.add_task(_send_raffle_email, request.email, request.name)

    return LeadResponse(**result._asdict())


_RAFFLE_EMAIL_TEMPLATE = (Path(__file__).parent / "raffle_email.html").read_text()
_WINNERS_EMAIL_TEMPLATE = (Path(__file__).parent / "raffle_winners_email.html").read_text()


def _send_winners_email(to_email: str) -> None:
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Congrats to the Nifty Attendance Raffle Winners!"
        msg["From"] = f"Nifty Ed Tools <{os.environ['GMAIL_USER']}>"
        msg["To"] = to_email
        msg.attach(MIMEText(_WINNERS_EMAIL_TEMPLATE, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(os.environ["GMAIL_USER"], os.environ["GMAIL_APP_PASSWORD"])
            server.sendmail(os.environ["GMAIL_USER"], to_email, msg.as_string())
        log.info("winners email sent to %s", to_email)
    except Exception:
        log.exception("failed to send winners email to %s", to_email)


@router.post("/winners-email-test", status_code=200)
async def test_winners_email(email: str = Body(..., embed=True)) -> dict:
    _send_winners_email(email)
    return {"sent": True, "to": email}

def _send_raffle_email(to_email: str, name: str) -> None:
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        html_body = _RAFFLE_EMAIL_TEMPLATE.replace("{name}", name)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "You're in the Nifty Attendance™ Raffle!"
        msg["From"] = f"Nifty Ed Tools <{os.environ['GMAIL_USER']}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(os.environ["GMAIL_USER"], os.environ["GMAIL_APP_PASSWORD"])
            server.sendmail(os.environ["GMAIL_USER"], to_email, msg.as_string())
        log.info("raffle email sent to %s", to_email)
    except Exception:
        log.exception("failed to send raffle email to %s", to_email)


@router.post("/{lead_id}/raffle", status_code=200)
async def trigger_raffle_email(lead_id: uuid.UUID) -> dict:
    async with engine.begin() as conn:
        row = await conn.execute(
            text("SELECT name, email FROM marketing.leads WHERE id = :id"),
            {"id": lead_id},
        )
        result = row.fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Lead not found")
    if not result.email:
        raise HTTPException(status_code=422, detail="Lead has no email address")

    _send_raffle_email(result.email, result.name)
    return {"sent": True, "to": result.email}


@router.patch("/{lead_id}/raffle-group", status_code=200)
async def update_raffle_group(lead_id: uuid.UUID, raffle_group: int = Body(..., embed=True)) -> dict:
    if raffle_group not in range(1, 6):
        raise HTTPException(status_code=422, detail="raffle_group must be between 1 and 5")
    async with engine.begin() as conn:
        row = await conn.execute(
            text("""
                UPDATE marketing.raffle SET raffle_group = :raffle_group
                WHERE lead_id = :lead_id
                RETURNING id, lead_id, raffle_location, raffle_group, created_at
            """),
            {"raffle_group": raffle_group, "lead_id": lead_id},
        )
        result = row.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Raffle entry not found")
    _save_raffle_parquet(result.id, result)
    return {"updated": True, "raffle_group": result.raffle_group}
# </product>
