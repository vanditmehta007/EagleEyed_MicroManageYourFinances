
from typing import Dict, Any, List, Optional
from backend.services.query_engine.query_service import QueryService
from backend.services.rag_service.retrieval_service import RetrievalService
from backend.models.query_models import QueryRequest
from backend.utils.logger import logger

# Initialize services
_query_service = QueryService()
_retrieval_service = RetrievalService()

def nl_query(query_text: str, client_id: str) -> Dict[str, Any]:
    """
    Execute a natural language query on financial data.
    """
    request = QueryRequest(
        query_text=query_text,
        client_id=client_id
    )
    result = _query_service.process_query(request)
    # Convert Pydantic model to dict
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__

def rag_lookup(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve relevant legal/compliance context from the knowledge base.
    """
    results = _retrieval_service.retrieve_context(query, limit=limit)
    # Convert Pydantic models to dicts
    return [result.model_dump() if hasattr(result, 'model_dump') else result.__dict__ for result in results]

# Tool Registry Export
QUERY_TOOLS = {
    "nl_query": nl_query,
    "rag_lookup": rag_lookup
}
