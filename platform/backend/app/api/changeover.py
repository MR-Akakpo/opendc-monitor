from fastapi import APIRouter
from app.services.changeover_live_service import get_changeover_live_data

router = APIRouter(prefix="/api/changeover", tags=["Change Over"])

@router.get("/live")
def changeover_live():
    return get_changeover_live_data()
