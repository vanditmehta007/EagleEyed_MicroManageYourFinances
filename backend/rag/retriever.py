from typing import List, Dict, Any
from backend.models.rag_models import RetrievalResult
from backend.rag.embedder import Embedder
from backend.rag.vector_store import VectorStore

class Retriever:
    """
    Performs similarity search on pgvector embeddings and returns top-k chunks for grounding.
    """

    def __init__(self):
        self.embedder = Embedder()
        self.vector_store = VectorStore()

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """
        Retrieves the most relevant chunks for a given query.
        """
        # 1. Generate embedding for the query
        query_embedding = self.embedder.generate_embedding(query)
        
        # 2. Perform similarity search in vector store
        return self.vector_store.search(query_embedding, top_k)

    def retrieve_with_filters(self, query: str, filters: Dict[str, Any], top_k: int = 5) -> List[RetrievalResult]:
        """
        Retrieves relevant chunks with metadata filtering.
        """
        query_embedding = self.embedder.generate_embedding(query)
        return self.vector_store.search(query_embedding, top_k, filters)
