from datetime import datetime
from pydantic import BaseModel
from typing import Dict, Any

class AdminLog(BaseModel):
    id: str
    action: str
    performed_by: str
    details: dict
    created_at: datetime

class SystemHealth(BaseModel):
    status: str
    timestamp: datetime
    components: Dict[str, Any]
