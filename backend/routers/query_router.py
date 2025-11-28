from fastapi import APIRouter, Depends
from backend.models.query_models import QueryRequest, QueryResult
from backend.services.query_engine.query_service import QueryService

router = APIRouter(prefix="/query", tags=["Query Engine"])

@router.post("/", response_model=QueryResult)
async def execute_query(
    request: QueryRequest, 
    service: QueryService = Depends()
):
    """
    Execute a natural language query on financial data.
    Returns table data, summary, and law references.
    """
    return service.process_query(request)
