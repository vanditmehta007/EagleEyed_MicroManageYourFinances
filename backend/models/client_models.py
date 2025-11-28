from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class ClientBase(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    business_type: Optional[str] = None
    assigned_ca_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ClientCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    business_type: Optional[str] = None

class ClientResponse(ClientBase):
    pass
