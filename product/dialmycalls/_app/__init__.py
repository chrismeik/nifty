from fastapi import APIRouter
from .texts import router as texts_router
from .raffle import router as raffle_router

router = APIRouter()
router.include_router(texts_router)
router.include_router(raffle_router)

__all__ = ["router"]
