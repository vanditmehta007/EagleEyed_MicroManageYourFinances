from fastapi import APIRouter, Depends
from typing import List
from backend.models.user_models import UserResponse, UserUpdate
from backend.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(service: UserService = Depends()):
    """
    Get profile of the currently logged-in user.
    """
    return service.get_current_user()

@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    updates: UserUpdate, 
    service: UserService = Depends()
):
    """
    Update profile details of the current user.
    """
    return service.update_current_user(updates)

@router.get("/", response_model=List[UserResponse])
async def list_users(service: UserService = Depends()):
    """
    List all users (Admin only).
    """
    return service.list_users()

@router.post("/{user_id}/link-client")
async def link_client_to_ca(
    user_id: str, 
    client_id: str, 
    service: UserService = Depends()
):
    """
    Link a CA user to a Client entity.
    """
    return service.link_client(user_id, client_id)
