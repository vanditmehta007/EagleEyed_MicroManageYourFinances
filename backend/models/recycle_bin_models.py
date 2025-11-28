from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class RecycleBinItem(BaseModel):
    id: str
    original_table: str
    original_id: str
    deleted_by_id: str
    deleted_by_role: str  # 'admin', 'client', 'ca'
    deleted_at: datetime
    expires_at: datetime
    item_metadata: Optional[dict] = None  # Store name, description etc for display

class RecycleBinResponse(RecycleBinItem):
    pass
