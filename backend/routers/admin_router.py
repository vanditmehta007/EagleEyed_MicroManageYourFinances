from fastapi import APIRouter, Depends, HTTPException
from typing import List
from backend.models.admin_models import AdminLog
from backend.services.admin.admin_service import AdminService


router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/logs", response_model=List[AdminLog])
async def get_admin_logs(
    limit: int = 100, 
    offset: int = 0, 
    service: AdminService = Depends()
):
    """
    Retrieve system/admin action logs.
    """
    return service.get_logs(limit, offset)

@router.get("/system-health")
async def check_system_health(service: AdminService = Depends()):
    """
    Check overall system health (DB, Redis, Workers).
    """
    return service.check_health()

@router.post("/trigger-maintenance")
async def trigger_maintenance(service: AdminService = Depends()):
    """
    Manually trigger system maintenance tasks.
    """
    return service.trigger_maintenance()

@router.delete("/permanent-delete/{resource_id}")
async def permanent_delete_resource(
    resource_id: str, 
    resource_type: str, 
    service: AdminService = Depends()
):
    """
    Permanently delete a soft-deleted resource.
    """
    return service.permanent_delete(resource_id, resource_type)
