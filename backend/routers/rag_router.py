from fastapi import APIRouter, Depends
from typing import List
from backend.models.rag_models import RetrievalResult
from backend.services.rag_service.rag_manager import RAGManager

router = APIRouter(prefix="/rag", tags=["RAG"])

@router.post("/reindex")
async def reindex_documents(service: RAGManager = Depends()):
    """
    Trigger a full re-indexing of all law and scheme documents.
    """
    return service.reindex_all()

@router.post("/refresh-laws")
async def refresh_laws(service: RAGManager = Depends()):
    """
    Crawl and update only the latest law changes.
    """
    return service.refresh_laws()

@router.get("/test-retrieval", response_model=List[RetrievalResult])
async def test_retrieval(
    query: str, 
    top_k: int = 5, 
    service: RAGManager = Depends()
):
    """
    Test the retrieval engine with a sample query.
    """
    return service.test_retrieval(query, top_k)
