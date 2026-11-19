from fastapi import APIRouter
from .routes import router as leads_router

router = APIRouter()
router.include_router(leads_router, prefix="/leads", tags=["marketing"])

__all__ = ["router"]
