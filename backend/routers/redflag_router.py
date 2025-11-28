from fastapi import APIRouter, Depends
from typing import List, Optional
from backend.models.redflag_models import RedFlag
from backend.services.red_flag_engine.anomaly_detector import AnomalyDetectorService

router = APIRouter(prefix="/redflags", tags=["Red Flags"])

@router.get("/", response_model=List[RedFlag])
async def get_red_flags(
    client_id: str, 
    resolved: Optional[bool] = False,
    service: AnomalyDetectorService = Depends()
):
    """
    Get all red flags for a client, optionally filtered by status.
    """
    return service.get_red_flags(client_id, resolved)

@router.post("/{flag_id}/resolve", response_model=RedFlag)
async def resolve_red_flag(
    flag_id: str, 
    resolution_note: str, 
    service: AnomalyDetectorService = Depends()
):
    """
    Mark a red flag as resolved with a note.
    """
    return service.resolve_flag(flag_id, resolution_note)

@router.post("/scan")
async def trigger_scan(
    client_id: str, 
    service: AnomalyDetectorService = Depends()
):
    """
    Manually trigger a red flag scan for a client.
    """
    return service.run_scan(client_id)
