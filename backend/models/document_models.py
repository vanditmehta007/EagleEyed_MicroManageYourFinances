from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel

class Document(BaseModel):
    id: str
    client_id: str
    file_path: str
    file_type: Literal["bank_statement", "invoice", "gst_json", "expense", "sales", "purchase", "payroll", "json_data", "expense_bill", "transaction_sheet"]
    original_filename: str
    metadata: Optional[dict] = None           # extracted vendor name, invoice no, dates, gstin etc
    folder_category: Optional[str]     # Bank/Expenses/GST/...
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class DocumentUploadResponse(BaseModel):
    id: str
    file_path: str
    file_type: str
