import json
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/changeover/control", tags=["Change Over Control"])

CONFIG = Path("runtime/changeover_control.json")

class ChangeoverControlRequest(BaseModel):
    lead_generator: str
    transfer_time_seconds: int

def read_config():
    if not CONFIG.exists():
        return {
            "lead_generator": "GENERATOR_A",
            "lag_generator": "GENERATOR_B",
            "transfer_time_seconds": 5
        }

    return json.loads(CONFIG.read_text(encoding="utf-8"))

def write_config(data):
    CONFIG.write_text(json.dumps(data, indent=2), encoding="utf-8")

@router.get("")
def get_control():
    return read_config()

@router.post("")
def update_control(payload: ChangeoverControlRequest):
    lead = payload.lead_generator.upper()

    if lead not in ["GENERATOR_A", "GENERATOR_B"]:
        lead = "GENERATOR_A"

    lag = "GENERATOR_B" if lead == "GENERATOR_A" else "GENERATOR_A"

    data = {
        "lead_generator": lead,
        "lag_generator": lag,
        "transfer_time_seconds": max(1, min(payload.transfer_time_seconds, 300))
    }

    write_config(data)

    return {
        "status": "UPDATED",
        "control": data
    }
