from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class SheetBase(BaseModel):
    name: str
    client_id: str
    financial_year: int

class SheetCreate(BaseModel):
    name: str
    client_id: str
    financial_year: int

class SheetResponse(BaseModel):
    id: str
    name: str
    client_id: str
    financial_year: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

class Sheet(SheetResponse):
    pass
