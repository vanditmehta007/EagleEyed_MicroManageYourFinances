from typing import Any, List
from pydantic import BaseModel

class SuccessResponse(BaseModel):
    success: bool = True
    data: Any

class ErrorResponse(BaseModel):
    success: bool = False
    error: str

class PaginatedResponse(BaseModel):
    success: bool = True
    data: List[Any]
    page: int
    per_page: int
    total: int
