from typing import List, Optional
from backend.rag.vector_store import VectorStore
from backend.services.rag_service.embedding_service import EmbeddingService
from backend.models.rag_models import RetrievalResult
from backend.utils.logger import logger

class RetrievalService:
    """
    Service for retrieving relevant context from the vector store.
    Handles embedding generation for queries, vector search, and result filtering.
    """

    def __init__(self):
        self.vector_store = VectorStore()
        self.embedding_service = EmbeddingService()
        
        # Default configuration
        self.DEFAULT_LIMIT = 5
        self.SIMILARITY_THRESHOLD = 0.75

    def retrieve_context(self, query: str, limit: int = None, threshold: float = None) -> List[RetrievalResult]:
        """
        Retrieve relevant law/scheme chunks for a given query.
        
        Args:
            query: The search query string.
            limit: Maximum number of results to return.
            threshold: Minimum similarity score (0 to 1).
            
        Returns:
            List of RetrievalResult objects containing text and metadata.
        """
        try:
            search_limit = limit or self.DEFAULT_LIMIT
            min_score = threshold or self.SIMILARITY_THRESHOLD
            
            # 1. Generate embedding for the query
            query_embedding = self.embedding_service.generate_embedding(query)
            
            if not query_embedding:
                logger.warning("Failed to generate embedding for query.")
                return []

            # 2. Search vector store
            results = self.vector_store.search(query_embedding, limit=search_limit)
            
            # 3. Filter by threshold
            filtered_results = [
                res for res in results 
                if res.score >= min_score
            ]
            
            logger.info(f"Retrieved {len(filtered_results)} chunks for query: '{query}' (Threshold: {min_score})")
            
            return filtered_results

        except Exception as e:
            logger.error(f"Error in retrieve_context: {str(e)}")
            return []

    def retrieve_for_compliance(self, transaction_desc: str, category: str = None) -> List[RetrievalResult]:
        """
        Specialized retrieval for compliance checking.
        Can optionally filter by category (e.g., 'GST', 'Income Tax').
        
        Args:
            transaction_desc: Description of the transaction.
            category: Optional category filter.
            
        Returns:
            List of relevant law chunks.
        """
        # Enhance query with category context if provided
        query = transaction_desc
        if category:
            query = f"{category} rules for {transaction_desc}"
            
        # Use a slightly lower threshold for compliance to ensure broad coverage
        return self.retrieve_context(query, limit=5, threshold=0.70)
