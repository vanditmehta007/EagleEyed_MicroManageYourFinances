from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class LedgerClassification(BaseModel):
    transaction_id: str
    ledger: str
    gst_applicable: bool
    tds_applicable: bool
    capital_expense: bool
    recurring: bool
    ai_confidence: float
    law_references: Optional[List[str]]
    created_at: datetime
