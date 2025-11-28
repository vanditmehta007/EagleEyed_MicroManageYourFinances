# backend/routers/settings_router.py

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger

router = APIRouter(prefix="/settings", tags=["Settings"])

class IntegrationCredentials(BaseModel):
    platform: str
    apiKey: str
    organizationId: str = None

@router.get("/integrations")
async def get_integration_credentials(request: Request):
    """
    Get saved integration credentials for the current user.
    """
    user_id = request.state.user_id
    
    try:
        # Fetch from database
        response = supabase.table("integration_credentials").select("*").eq("user_id", user_id).execute()
        
        if not response.data:
            return {}
        
        # Organize by platform
        credentials = {}
        for cred in response.data:
            credentials[cred["platform"]] = {
                "apiKey": cred["api_key"],
                "organizationId": cred.get("organization_id"),
                "platform": cred["platform"]
            }
        
        return credentials
        
    except Exception as e:
        logger.error(f"Failed to fetch integration credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch credentials")

@router.post("/integrations")
async def save_integration_credentials(
    request: Request,
    credentials: IntegrationCredentials
):
    """
    Save or update integration credentials for the current user.
    """
    user_id = request.state.user_id
    
    try:
        # Check if credentials already exist
        existing = supabase.table("integration_credentials").select("id").eq("user_id", user_id).eq("platform", credentials.platform).execute()
        
        data = {
            "user_id": user_id,
            "platform": credentials.platform,
            "api_key": credentials.apiKey,
            "organization_id": credentials.organizationId
        }
        
        if existing.data:
            # Update existing
            response = supabase.table("integration_credentials").update(data).eq("id", existing.data[0]["id"]).execute()
        else:
            # Insert new
            response = supabase.table("integration_credentials").insert(data).execute()
        
        return {"success": True, "message": "Credentials saved successfully"}
        
    except Exception as e:
        logger.error(f"Failed to save integration credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to save credentials")

@router.delete("/integrations/{platform}")
async def delete_integration_credentials(
    platform: str,
    request: Request
):
    """
    Delete integration credentials for a specific platform.
    """
    user_id = request.state.user_id
    
    try:
        supabase.table("integration_credentials").delete().eq("user_id", user_id).eq("platform", platform).execute()
        return {"success": True, "message": "Credentials deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete integration credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete credentials")
