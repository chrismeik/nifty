from fastapi import APIRouter
from .routes import router as trigger_router
from .tasks.sources.routes import router as sources_router

router = APIRouter()
router.include_router(trigger_router)
router.include_router(sources_router, prefix="/tasks/sources", tags=["nifty-tasks"])

__all__ = ["router"]
