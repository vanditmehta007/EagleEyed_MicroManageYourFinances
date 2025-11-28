from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel
from typing import Literal

class TransactionBase(BaseModel):
    date: date
    description: str
    amount: float
    type: Literal["credit", "debit"]
    ledger: Optional[str] = None
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None

class TransactionCreate(TransactionBase):
    sheet_id: str

class TransactionUpdate(BaseModel):
    date: Optional[date] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    type: Optional[Literal["credit", "debit"]] = None
    ledger: Optional[str] = None
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None

class TransactionResponse(BaseModel):
    id: str
    sheet_id: str
    date: date
    description: str
    amount: float
    type: Literal["credit", "debit"]
    ledger: Optional[str] = None
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    gst_applicable: Optional[bool] = None
    tds_applicable: Optional[bool] = None
    capital_expense: Optional[bool] = None
    recurring: Optional[bool] = None
    ai_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

class Transaction(TransactionResponse):
    pass
