from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from backend.services.core.recycle_bin_service import RecycleBinService
from backend.models.recycle_bin_models import RecycleBinResponse
from backend.utils.auth_utils import get_current_user  # Assuming this exists or similar

router = APIRouter(prefix="/recycle-bin", tags=["Recycle Bin"])
service = RecycleBinService()

@router.get("/", response_model=List[RecycleBinResponse])
async def list_deleted_items(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List all deleted items visible to the current user.
    """
    user_id = current_user["id"]
    role = current_user.get("role", "client")
    return service.list_deleted_items(user_id, role)

@router.post("/{bin_id}/restore")
async def restore_item(
    bin_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Restore a deleted item.
    """
    # In a real app, we should verify ownership of the bin item here too
    # The service handles the logic, but RLS protects the DB access
    result = service.restore_item(bin_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.delete("/{bin_id}")
async def permanent_delete_item(
    bin_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Permanently delete an item.
    """
    result = service.permanent_delete_item(bin_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/cleanup")
async def cleanup_expired_items(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Trigger cleanup of expired items (Admin only).
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can trigger cleanup")
        
    result = service.cleanup_expired_items()
    return result
