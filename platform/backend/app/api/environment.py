from fastapi import APIRouter
from app.services.environment_live_service import get_environment_live_data

router = APIRouter(prefix="/api/environment", tags=["Environment Sensor"])

@router.get("/live")
def environment_live():
    return get_environment_live_data()
