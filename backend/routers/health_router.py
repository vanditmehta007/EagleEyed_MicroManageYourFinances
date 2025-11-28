from fastapi import APIRouter
from backend.models.admin_models import SystemHealth
from backend.services.admin.system_monitor import SystemMonitor

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=SystemHealth)
async def health_check():
    """
    Basic application health check (Liveness probe).
    """
    return SystemMonitor.get_basic_health()

@router.get("/status", response_model=SystemHealth)
async def system_status():
    """
    Detailed system status including DB and Redis connectivity (Readiness probe).
    """
    return SystemMonitor.get_detailed_status()
