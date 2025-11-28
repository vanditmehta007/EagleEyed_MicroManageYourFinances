from typing import Literal
from datetime import datetime
from pydantic import BaseModel

class RedFlag(BaseModel):
    id: str
    transaction_id: str
    flag_type: Literal[
        "large_cash",
        "duplicate_invoice",
        "gst_mismatch",
        "missing_invoice",
        "suspicious_vendor",
        "anomaly"
    ]
    severity: Literal["low", "medium", "high"]
    message: str
    created_at: datetime
    resolved: bool = False
