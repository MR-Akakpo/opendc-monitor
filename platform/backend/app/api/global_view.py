from fastapi import APIRouter
from app.services.global_live_service import get_global_live_data

router = APIRouter(prefix="/api/global-view", tags=["Global View"])

@router.get("/live")
def global_view_live():
    return get_global_live_data()
