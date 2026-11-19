import os
from fastapi import APIRouter


def _build_router() -> APIRouter:
    r = APIRouter(prefix="/texts", tags=["dialmycalls-texts"])
    if os.getenv("DIALMYCALLS_MOCK", "").lower() in ("1", "true", "yes"):
        from .send_spoofed import router as send_router
    else:
        from .send import router as send_router
    r.include_router(send_router)
    return r


router = _build_router()
__all__ = ["router"]
