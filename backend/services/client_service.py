from typing import List, Optional
from datetime import datetime
import uuid
from fastapi import HTTPException
from backend.models.client_models import ClientCreate, ClientResponse
from backend.config import settings
from supabase import create_client

class ClientService:
    """
    Service for managing client entities and CA assignments.
    """
    
    def __init__(self):
        self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

    def create_client(self, client_data: ClientCreate, user_id: str) -> ClientResponse:
        """
        Create a new client entity.
        """
        try:
            client_id = str(uuid.uuid4())
            
            new_client = {
                "id": client_id,
                "name": client_data.name,
                "email": client_data.email,
                "phone": client_data.phone,
                "gstin": client_data.gstin,
                "pan": client_data.pan,
                "business_type": client_data.business_type,
                "created_by": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            data = self.supabase.table("clients").insert(new_client).execute()
            
            if not data.data:
                raise HTTPException(status_code=500, detail="Failed to create client")
            
            return ClientResponse(**data.data[0])
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def get_client(self, client_id: str) -> ClientResponse:
        """
        Retrieve a specific client by ID.
        """
        try:
            data = self.supabase.table("clients").select("*").eq("id", client_id).execute()
            
            if not data.data:
                raise HTTPException(status_code=404, detail="Client not found")
            
            return ClientResponse(**data.data[0])
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def list_clients(self, user_id: str, role: str) -> List[ClientResponse]:
        """
        List all clients accessible to the user.
        """
        try:
            query = self.supabase.table("clients").select("*")
            
            # If user is a client, only show their own record
            if role == "client":
                query = query.eq("created_by", user_id)
            # If user is a CA, show clients assigned to them
            elif role == "ca":
                query = query.eq("assigned_ca_id", user_id)
            # Admin sees all
            
            data = query.execute()
            
            return [ClientResponse(**client) for client in data.data]
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def assign_ca(self, client_id: str, ca_id: str) -> ClientResponse:
        """
        Assign a CA to a client.
        """
        try:
            data = self.supabase.table("clients").update({
                "assigned_ca_id": ca_id,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", client_id).execute()
            
            if not data.data:
                raise HTTPException(status_code=404, detail="Client not found")
            
            return ClientResponse(**data.data[0])
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def update_client(self, client_id: str, update_data: dict) -> ClientResponse:
        """
        Update client information.
        """
        try:
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            data = self.supabase.table("clients").update(update_data).eq("id", client_id).execute()
            
            if not data.data:
                raise HTTPException(status_code=404, detail="Client not found")
            
            return ClientResponse(**data.data[0])
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def delete_client(self, client_id: str) -> dict:
        """
        Soft delete a client.
        """
        try:
            data = self.supabase.table("clients").update({
                "deleted_at": datetime.utcnow().isoformat()
            }).eq("id", client_id).execute()
            
            if not data.data:
                raise HTTPException(status_code=404, detail="Client not found")
            
            return {"success": True, "message": "Client deleted successfully"}
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
