"""
HTTP trigger for the nifty attendance pipeline.
Enqueues the Dramatiq worker immediately — does not run the pipeline inline.
"""

from datetime import date, datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class PipelineRunRequest(BaseModel):
    school_id: int
    target_date: date | None = None


class PipelineRunResponse(BaseModel):
    queued: bool
    school_id: int
    target_date: date


@router.post("/run", response_model=PipelineRunResponse)
async def trigger_pipeline(request: PipelineRunRequest) -> PipelineRunResponse:
    from notify._app.worker import run_notify_task

    target_date = request.target_date or datetime.now(timezone.utc).date()
    run_notify_task.send(request.school_id, target_date.isoformat())

    return PipelineRunResponse(
        queued=True,
        school_id=request.school_id,
        target_date=target_date,
    )
