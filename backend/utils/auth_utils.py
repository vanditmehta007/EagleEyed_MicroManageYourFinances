from fastapi import Header, HTTPException
from typing import Dict, Any, Optional

async def get_current_user(x_user_id: Optional[str] = Header(None, alias="X-User-Id"), x_role: Optional[str] = Header("client", alias="X-Role")) -> Dict[str, Any]:
    """
    Mock authentication dependency.
    In production, this should validate a JWT token from the Authorization header.
    For now, it trusts X-User-Id and X-Role headers for internal testing.
    """
    if not x_user_id:
        # For development ease, if no header, return a dummy admin user
        # raise HTTPException(status_code=401, detail="Missing authentication")
        return {"id": "dummy-user-id", "role": "admin", "email": "admin@example.com"}
        
    return {
        "id": x_user_id,
        "role": x_role,
        "email": "user@example.com"
    }
