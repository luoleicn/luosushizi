"""API router."""

from fastapi import APIRouter

from app.api import auth
from app.api import characters
from app.api import study
from app.api import stats

router = APIRouter()
router.include_router(auth.router)
router.include_router(characters.router)
router.include_router(study.router)
router.include_router(stats.router)
