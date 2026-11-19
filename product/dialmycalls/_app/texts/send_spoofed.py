"""
Spoofed DialMyCalls /send endpoint.

Returns a realistic success response without hitting the real API.
Activate by setting DIALMYCALLS_MOCK=true in the environment.
"""

import uuid
from fastapi import APIRouter
from .send import SendTextRequest, SendTextResponse

router = APIRouter()


@router.post("/send")
async def send_text(request: SendTextRequest) -> SendTextResponse:
    return SendTextResponse(
        success=True,
        broadcast_id=str(uuid.uuid4()),
        message=f"Text queued for {request.to}",
    )
