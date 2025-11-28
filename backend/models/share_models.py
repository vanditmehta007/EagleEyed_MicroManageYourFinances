from typing import Literal
from datetime import datetime
from pydantic import BaseModel

class ShareTokenCreate(BaseModel):
    resource_type: Literal["sheet", "document", "client"]
    resource_id: str
    expires_in_hours: int = 72

class ShareTokenModel(BaseModel):
    token: str
    resource_type: Literal["sheet", "document", "client"]
    resource_id: str
    expires_at: datetime
    max_uses: int
    current_uses: int
