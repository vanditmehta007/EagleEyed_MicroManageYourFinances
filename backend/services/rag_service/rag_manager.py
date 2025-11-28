from typing import Dict, Any, List
from backend.services.rag_service.retrieval_service import RetrievalService
from backend.rag.vector_store import VectorStore
from backend.workers.law_crawler_worker import LawCrawlerWorker
from backend.workers.scheme_crawler_worker import SchemeCrawlerWorker
from backend.utils.logger import logger

class RAGManager:
    """
    High-level manager for RAG (Retrieval-Augmented Generation) operations.
    
    Orchestrates:
    - Indexing of law/scheme documents (via Workers)
    - Retrieval of relevant context (via RetrievalService)
    - Vector store management
    - Periodic refresh of legal data
    """

    def __init__(self):
        self.retrieval_service = RetrievalService()
        self.vector_store = VectorStore()
        # Initialize workers for indexing tasks
        self.law_worker = LawCrawlerWorker()
        self.scheme_worker = SchemeCrawlerWorker()

    async def reindex_all(self) -> Dict[str, Any]:
        """
        Trigger full re-indexing of all law and scheme documents.
        This is a heavy operation and should be run as a background task.
        """
        try:
            logger.info("Starting full re-indexing...")
            
            # 1. Run Law Crawlers
            law_results = await self.law_worker.run_all_crawlers()
            
            # 2. Run Scheme Crawlers
            scheme_results = await self.scheme_worker.run_scheme_crawl()
            
            return {
                "status": "success",
                "message": "Re-indexing completed",
                "law_results": law_results,
                "scheme_results": scheme_results
            }
        except Exception as e:
            logger.error(f"Re-indexing failed: {e}")
            return {"status": "error", "message": str(e)}

    async def refresh_laws(self) -> Dict[str, Any]:
        """
        Refresh all law sources (GST, Income Tax, etc.).
        """
        try:
            logger.info("Refreshing law data...")
            results = await self.law_worker.run_all_crawlers()
            return {"status": "success", "results": results}
        except Exception as e:
            logger.error(f"Law refresh failed: {e}")
            return {"status": "error", "message": str(e)}

    def test_retrieval(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Test retrieval for a given query.
        Useful for debugging RAG performance.
        """
        try:
            results = self.retrieval_service.retrieve_context(query, limit=top_k)
            
            # Convert RetrievalResult objects to dicts for API response
            return [
                {
                    "text": res.text,
                    "score": res.score,
                    "metadata": res.metadata
                }
                for res in results
            ]
        except Exception as e:
            logger.error(f"Test retrieval failed: {e}")
            return []

    def get_vector_store_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        """
        # Since VectorStore doesn't have a stats method yet, we'll implement a basic one or placeholder
        # Ideally, VectorStore should have a `get_stats()` method.
        # For now, we return a placeholder or call a hypothetical method if we added it.
        
        # Assuming we might add it later or use a direct query if we had access to the client here.
        # But VectorStore encapsulates the client.
        
        return {
            "status": "active",
            "message": "Stats retrieval not yet implemented in VectorStore"
        }
