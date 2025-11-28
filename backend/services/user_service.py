from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException
from backend.models.user_models import UserProfile, UserUpdate
from backend.utils.supabase_client import supabase

class UserService:
    """
    Service for managing user profiles and CA-client relationships.
    """

    def get_profile(self, user_id: str) -> UserProfile:
        """
        Retrieve user profile by ID.
        """
        try:
            data = supabase.table("users").select("*").eq("id", user_id).execute()
            
            if not data.data:
                raise HTTPException(status_code=404, detail="User not found")
            
            return UserProfile(**data.data[0])
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def update_profile(self, user_id: str, update: UserUpdate) -> UserProfile:
        """
        Update user profile.
        """
        try:
            update_data = update.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            data = supabase.table("users").update(update_data).eq("id", user_id).execute()
            
            if not data.data:
                raise HTTPException(status_code=404, detail="User not found")
            
            return UserProfile(**data.data[0])
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def list_users(self, role: Optional[str] = None) -> List[UserProfile]:
        """
        List all users, optionally filtered by role.
        """
        try:
            query = supabase.table("users").select("*")
            
            if role:
                query = query.eq("role", role)
            
            data = query.execute()
            
            return [UserProfile(**user) for user in data.data]
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def link_ca_to_client(self, ca_id: str, client_id: str) -> dict:
        """
        Link a CA to a client.
        """
        try:
            # Update client record with CA assignment
            data = supabase.table("clients").update({
                "assigned_ca_id": ca_id,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", client_id).execute()
            
            if not data.data:
                raise HTTPException(status_code=404, detail="Client not found")
            
            return {"success": True, "message": "CA linked to client successfully"}
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
