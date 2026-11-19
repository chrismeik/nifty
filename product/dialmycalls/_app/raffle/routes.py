"""
DialMyCalls endpoints for the raffle SMS sequence.

Each endpoint is pre-configured with message content and send timing.
Accepts a contacts list and fires the appropriate broadcast.
"""

import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

from dialmycalls._app.auth import get_auth, get_vanity_number_id, BASE_URL

router = APIRouter()

_CT = ZoneInfo("America/Chicago")


class RaffleMessageRequest(BaseModel):
    contacts: list[dict]


class RaffleMessageResponse(BaseModel):
    success: bool
    broadcast_id: str
    send_at: str


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _next_weekday_9am_ct(weekday: int) -> datetime:
    """Return the next occurrence of weekday (0=Mon) at 9:00 AM CT as UTC datetime."""
    now_ct = datetime.now(_CT)
    days_ahead = (weekday - now_ct.weekday()) % 7
    if days_ahead == 0 and (now_ct.hour > 9 or (now_ct.hour == 9 and now_ct.minute > 0)):
        days_ahead = 7
    target_ct = now_ct.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=days_ahead)
    return target_ct.astimezone(timezone.utc)


async def _send(messages: list[str], contacts: list[dict], send_at: datetime | None, send_immediately: bool) -> str:
    name = f"raffle_{uuid.uuid4().hex[:8]}"
    payload = {
        "name":             name,
        "vanitynumber_id":  get_vanity_number_id(),
        "messages":         messages,
        "contacts":         contacts,
        "send_immediately": send_immediately,
    }
    if send_at:
        payload["send_at"] = send_at.isoformat()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/service/text",
            json=payload,
            auth=get_auth(),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=30.0,
        )
    response.raise_for_status()
    return str(response.json().get("id", ""))


@router.post("/message-1", response_model=RaffleMessageResponse)
async def send_message_1(request: RaffleMessageRequest) -> RaffleMessageResponse:
    """Welcome to the raffle — sent immediately."""
    messages = [
        "Welcome to the Nifty Attendance™ raffle! We're excited to show you how it works. Stay tuned for more messages.",
    ]
    send_at = _now_utc()
    broadcast_id = await _send(messages, request.contacts, send_at=None, send_immediately=True)
    return RaffleMessageResponse(success=True, broadcast_id=broadcast_id, send_at=send_at.isoformat())


@router.post("/message-2", response_model=RaffleMessageResponse)
async def send_message_2(request: RaffleMessageRequest) -> RaffleMessageResponse:
    """About Nifty — sent 1 minute after signup."""
    messages = [
        "Here's what Nifty Attendance™ does: it automatically notifies parents the moment an unexcused absence is recorded. Over the next few days you'll receive sample messages.",
    ]
    send_at = _now_utc() + timedelta(minutes=1)
    broadcast_id = await _send(messages, request.contacts, send_at=send_at, send_immediately=False)
    return RaffleMessageResponse(success=True, broadcast_id=broadcast_id, send_at=send_at.isoformat())


@router.post("/message-3", response_model=RaffleMessageResponse)
async def send_message_3(request: RaffleMessageRequest) -> RaffleMessageResponse:
    """Unexcused absence example — sent 1 hour after signup."""
    messages = [
        (
            "Liam Espinoza — Unexcused Absence\n"
            "10/23/26\n\n"
            "Please contact the school office before 8:30 AM to resolve this, otherwise it will remain unexcused.\n"
            "(913)352-8531\n\n"
            "************************\n\n"
            "2026-27 Absences: 5\n"
            "Unexcused: 1 · Parent Excused: 3 · Other Excused: 1"
        ),
    ]
    send_at = _now_utc() + timedelta(hours=1)
    broadcast_id = await _send(messages, request.contacts, send_at=send_at, send_immediately=False)
    return RaffleMessageResponse(success=True, broadcast_id=broadcast_id, send_at=send_at.isoformat())


@router.post("/message-4", response_model=RaffleMessageResponse)
async def send_message_4(request: RaffleMessageRequest) -> RaffleMessageResponse:
    """Attendance streak celebration — next Monday at 9:00 AM CT."""
    messages = [
        (
            "Mia Johnson — Attendance Streak 🏆\n"
            "10/23/26\n\n"
            "She is on track to earn an extra recess with perfect or near-perfect attendance for October. "
            "Mia keeps rocking her school attendance! 🎸\n\n"
            "Only 5 more days until you break your personal record! Way to go, Mia!!!\n\n"
            "************************\n\n"
            "Current Streak: 42 days\n"
            "Record Streak: 46 days"
        ),
    ]
    send_at = _next_weekday_9am_ct(0)  # Monday
    broadcast_id = await _send(messages, request.contacts, send_at=send_at, send_immediately=False)
    return RaffleMessageResponse(success=True, broadcast_id=broadcast_id, send_at=send_at.isoformat())


@router.post("/message-5", response_model=RaffleMessageResponse)
async def send_message_5(request: RaffleMessageRequest) -> RaffleMessageResponse:
    """Encouragement to rebuild a streak — next Tuesday at 9:00 AM CT."""
    messages = [
        (
            "Mia Johnson — Attendance Update\n"
            "10/23/26\n\n"
            "We missed Mia this week. We're always glad when she's here — it's time to start building that streak back up!\n\n"
            "************************\n\n"
            "Current Streak: 3 days\n"
            "Record Streak: 59 days"
        ),
    ]
    send_at = _next_weekday_9am_ct(1)  # Tuesday
    broadcast_id = await _send(messages, request.contacts, send_at=send_at, send_immediately=False)
    return RaffleMessageResponse(success=True, broadcast_id=broadcast_id, send_at=send_at.isoformat())


@router.post("/message-6", response_model=RaffleMessageResponse)
async def send_message_6(request: RaffleMessageRequest) -> RaffleMessageResponse:
    """Trajectory warning: running low on excused absences — next Wednesday at 9:00 AM CT."""
    messages = [
        (
            "Henry Garcia — Attendance Alert\n"
            "10/23/26\n\n"
            "Based on Henry's attendance trajectory, he will be all out of Parent Excused Absences by February. "
            "Please contact the attendance secretary for needed support.\n"
            "(913)352-8532\n\n"
            "************************\n\n"
            "2026-27 Parent Excused: 8 of 10 used\n"
            "Unexcused: 1 · Other Excused: 1"
        ),
    ]
    send_at = _next_weekday_9am_ct(2)  # Wednesday
    broadcast_id = await _send(messages, request.contacts, send_at=send_at, send_immediately=False)
    return RaffleMessageResponse(success=True, broadcast_id=broadcast_id, send_at=send_at.isoformat())


@router.post("/message-7", response_model=RaffleMessageResponse)
async def send_message_7(request: RaffleMessageRequest) -> RaffleMessageResponse:
    """District monthly report example — next Thursday at 9:00 AM CT."""
    messages = [
        (
            "Springfield R-XII — Monthly Report\n"
            "October 2026\n\n"
            "District Attendance %:\n"
            "October 25': 91%\n"
            "October 26': 93%\n\n"
            "************************\n\n"
            "Increase in Funding: $17,453.23\n"
            "Annual Projection: $163,077.42"
        ),
    ]
    send_at = _next_weekday_9am_ct(3)  # Thursday
    broadcast_id = await _send(messages, request.contacts, send_at=send_at, send_immediately=False)
    return RaffleMessageResponse(success=True, broadcast_id=broadcast_id, send_at=send_at.isoformat())
