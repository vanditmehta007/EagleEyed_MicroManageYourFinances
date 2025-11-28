from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from typing import Literal

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: Literal["client", "ca", "admin"] = "client"
    phone: Optional[str] = None

class UserProfile(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    role: Literal["client", "ca", "admin"]
    phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None

class UserResponse(UserProfile):
    pass
