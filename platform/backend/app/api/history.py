from fastapi import APIRouter, Query
from app.services.history_service import get_history_data

router = APIRouter(prefix="/api/history", tags=["History Engine"])

@router.get("")
def history(
    system: str = Query(...),
    equipment: str = Query(...),
    metric: str = Query(...),
    period: str = Query("24h")
):
    return get_history_data(system, equipment, metric, period)
