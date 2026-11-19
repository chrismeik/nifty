import os
from fastapi import APIRouter


def _build_router() -> APIRouter:
    r = APIRouter(prefix="/raffle", tags=["dialmycalls-raffle"])
    if os.getenv("DIALMYCALLS_MOCK", "").lower() in ("1", "true", "yes"):
        from .routes_spoofed import router as raffle_router
    else:
        from .routes import router as raffle_router
    r.include_router(raffle_router)
    return r


router = _build_router()
__all__ = ["router"]
