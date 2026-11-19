from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
from datetime import datetime, timezone
from ..auth import get_auth, get_vanity_number_id, BASE_URL

router = APIRouter()


class SendTextRequest(BaseModel):
    to: str
    message: str
    name: Optional[str] = None
    send_immediately: bool = True


class SendTextResponse(BaseModel):
    success: bool
    broadcast_id: str
    message: str


@router.post("/send")
async def send_text(request: SendTextRequest) -> SendTextResponse:
    name = request.name or f"text_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    payload = {
        "name": name,
        "vanitynumber_id": get_vanity_number_id(),
        "message": request.message,
        "contacts": [{"phone": request.to}],
        "send_immediately": request.send_immediately,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/service/text",
            json=payload,
            auth=get_auth(),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=30.0,
        )

    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=response.status_code,
            detail=f"DialMyCalls error: {response.text}",
        )

    data = response.json()

    return SendTextResponse(
        success=True,
        broadcast_id=str(data.get("results", {}).get("id", "")),
        message=f"Text queued for {request.to}",
    )
