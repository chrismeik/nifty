"""
Steps 1-3 — Pull from SIS, stage, and transform attendance data.

Exposes SIS ingestion as a standalone HTTP endpoint so it can be triggered
independently or called by the pipeline orchestrator.
"""

import logging
from datetime import date, datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from _app._postgres import engine
from .adapters.registry import get_adapter

router = APIRouter()
log = logging.getLogger(__name__)


class SourcesPullRequest(BaseModel):
    school_id: int
    target_date: date | None = None


class SourcesPullResponse(BaseModel):
    school_id: int
    target_date: date
    meta: dict


@router.post("/pull", response_model=SourcesPullResponse)
async def pull_sources(request: SourcesPullRequest) -> SourcesPullResponse:
    target_date = request.target_date or datetime.now(timezone.utc).date()
    sis_type, config = await _get_sis_config(request.school_id)
    adapter = get_adapter(sis_type, config)

    data, fetch_meta   = adapter.fetch(request.school_id, target_date)
    stage_meta         = await adapter.stage(data)
    transform_meta     = await adapter.transform(data, target_date)

    meta = {"fetch": fetch_meta, "stage": stage_meta, "transform": transform_meta}
    log.info("sources pull complete: school=%s date=%s", request.school_id, target_date)
    return SourcesPullResponse(school_id=request.school_id, target_date=target_date, meta=meta)


async def _get_sis_config(school_id: int) -> tuple[str, dict]:
    async with engine.connect() as conn:
        row = await conn.execute(
            text("""
                SELECT sis_type, connection_config
                FROM core.sis_configurations
                WHERE school_id = :school_id
                  AND is_active = TRUE
                LIMIT 1
            """),
            {"school_id": school_id},
        )
        result = row.fetchone()

    if not result:
        raise ValueError(f"No active SIS configuration found for school_id={school_id}")

    return result.sis_type, result.connection_config
