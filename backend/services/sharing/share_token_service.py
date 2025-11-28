# backend/services/sharing/share_token_service.py

from typing import Dict, Any, Optional
import uuid
from datetime import datetime, timedelta
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger
import hashlib

class ShareTokenService:
    """
    Service for generating secure share tokens for reports and documents.
    
    Generates:
    - Time-limited share links
    - Password-protected links
    - View-only access tokens
    """

    def __init__(self) -> None:
        # Supabase client is imported globally
        pass

    def create_share_link(
        self, 
        resource_type: str, 
        resource_id: str, 
        expiry_hours: int = 24,
        password: str = None
    ) -> Dict[str, Any]:
        """
        Create a shareable link for a resource.
        
        Args:
            resource_type: Type of resource (report, document, sheet).
            resource_id: ID of the resource.
            expiry_hours: Link expiry time in hours.
            password: Optional password protection.
            
        Returns:
            Share link dict with token and URL.
        """
        try:
            # Generate unique token
            token = str(uuid.uuid4())
            
            # Calculate expiry time
            expiry_time = datetime.utcnow() + timedelta(hours=expiry_hours)
            
            # Hash password if provided
            password_hash = None
            if password:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Store share token in database
            data = {
                "token": token,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "expires_at": expiry_time.isoformat(),
                "password_hash": password_hash,
                "created_at": datetime.utcnow().isoformat(),
                "revoked": False
            }
            
            response = supabase.table("share_tokens").insert(data).execute()
            
            if not response.data:
                raise Exception("Failed to insert share link")
            
            return {
                "token": token,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "expires_at": expiry_time,
                "max_uses": 100,  # Default value for model compatibility
                "current_uses": 0  # Default value for model compatibility
            }
            
        except Exception as e:
            logger.error(f"Failed to create share link: {e}")
            raise Exception(f"Failed to create share link: {str(e)}")

    def create_token(self, resource_type: str, resource_id: str, expires_in_hours: int = 24) -> Dict[str, Any]:
        """
        Alias for create_share_link to match router expectations.
        """
        return self.create_share_link(resource_type, resource_id, expires_in_hours)

    def validate_token(self, token: str, password: str = None) -> Dict[str, Any]:
        """
        Validate a share token and return resource details.
        
        Args:
            token: Share token.
            password: Optional password if link is protected.
            
        Returns:
            Validation result dict with resource details or error.
        """
        try:
            # Fetch token from database
            response = supabase.table("share_tokens").select("*").eq("token", token).single().execute()
            
            if not response.data:
                return {"valid": False, "error": "Invalid token"}
            
            link_data = response.data
            
            # Check if revoked
            if link_data.get("revoked"):
                return {"valid": False, "error": "Link has been revoked"}
            
            # Check expiry
            expires_at_str = link_data["expires_at"]
            # Parse the datetime string and ensure it's timezone-aware
            if isinstance(expires_at_str, str):
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            else:
                expires_at = expires_at_str
            
            # Make current time timezone-aware (UTC)
            from datetime import timezone
            now_utc = datetime.now(timezone.utc)
            
            # Ensure expires_at is timezone-aware
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if now_utc > expires_at:
                return {"valid": False, "error": "Link has expired"}
            
            # Verify password if required
            if link_data.get("password_hash"):
                if not password:
                    return {"valid": False, "error": "Password required", "password_required": True}
                
                input_hash = hashlib.sha256(password.encode()).hexdigest()
                if input_hash != link_data["password_hash"]:
                    return {"valid": False, "error": "Incorrect password"}
            
            # Fetch resource details based on type
            resource_type = link_data["resource_type"]
            resource_id = link_data["resource_id"]
            resource_data = {}
            
            if resource_type == "document":
                res = supabase.table("documents").select("*").eq("id", resource_id).single().execute()
                resource_data = res.data
            elif resource_type == "sheet":
                res = supabase.table("sheets").select("*").eq("id", resource_id).single().execute()
                resource_data = res.data
            # Add other resource types as needed
            
            return {
                "valid": True,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "resource_data": resource_data
            }
            
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return {"valid": False, "error": str(e)}

    def revoke_token(self, token: str) -> Dict[str, Any]:
        """
        Revoke a share token.
        
        Args:
            token: Share token to revoke.
            
        Returns:
            Revocation status dict.
        """
        try:
            response = supabase.table("share_tokens").update({"revoked": True}).eq("token", token).execute()
            
            if response.data:
                return {"success": True, "message": "Token revoked successfully"}
            else:
                return {"success": False, "message": "Token not found"}
                
        except Exception as e:
            logger.error(f"Token revocation failed: {e}")
            return {"success": False, "error": str(e)}
