"""
Spoofed raffle endpoints — returns realistic responses without hitting DialMyCalls.
Activated when DIALMYCALLS_MOCK=true.
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter
from .routes import RaffleMessageRequest, RaffleMessageResponse, _now_utc, _next_weekday_9am_ct

router = APIRouter()


def _mock(send_at: datetime) -> RaffleMessageResponse:
    return RaffleMessageResponse(
        success=True,
        broadcast_id=str(uuid.uuid4()),
        send_at=send_at.isoformat(),
    )


@router.post("/message-1", response_model=RaffleMessageResponse)
async def send_message_1(request: RaffleMessageRequest) -> RaffleMessageResponse:
    return _mock(_now_utc())

@router.post("/message-2", response_model=RaffleMessageResponse)
async def send_message_2(request: RaffleMessageRequest) -> RaffleMessageResponse:
    from datetime import timedelta
    return _mock(_now_utc() + timedelta(minutes=1))

@router.post("/message-3", response_model=RaffleMessageResponse)
async def send_message_3(request: RaffleMessageRequest) -> RaffleMessageResponse:
    from datetime import timedelta
    return _mock(_now_utc() + timedelta(hours=1))

@router.post("/message-4", response_model=RaffleMessageResponse)
async def send_message_4(request: RaffleMessageRequest) -> RaffleMessageResponse:
    return _mock(_next_weekday_9am_ct(0))

@router.post("/message-5", response_model=RaffleMessageResponse)
async def send_message_5(request: RaffleMessageRequest) -> RaffleMessageResponse:
    return _mock(_next_weekday_9am_ct(1))

@router.post("/message-6", response_model=RaffleMessageResponse)
async def send_message_6(request: RaffleMessageRequest) -> RaffleMessageResponse:
    return _mock(_next_weekday_9am_ct(2))

@router.post("/message-7", response_model=RaffleMessageResponse)
async def send_message_7(request: RaffleMessageRequest) -> RaffleMessageResponse:
    return _mock(_next_weekday_9am_ct(3))
