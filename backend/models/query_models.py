from typing import Optional, List
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    filters: Optional[dict]

class QueryResult(BaseModel):
    table: List[dict]
    summary: str
    law_references: Optional[List[str]]
