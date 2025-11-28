from typing import List, Dict, Any, Optional
from backend.models.rag_models import EmbeddingChunk, RetrievalResult
from backend.utils.supabase_client import supabase

class VectorStore:
    """
    Interface for storing, updating, and querying embeddings in pgvector via Supabase.
    """

    def store_embeddings(self, chunks: List[EmbeddingChunk]):
        """
        Stores a batch of embedding chunks into the database.
        """
        if not chunks:
            return

        # Prepare data for insertion
        data = [
            {
                "id": chunk.id,
                "source": chunk.source,
                "chunk_text": chunk.chunk_text,
                "embedding": chunk.embedding,
                # "metadata": chunk.metadata # If metadata field exists
            }
            for chunk in chunks
        ]

        try:
            # Assuming table 'embeddings' exists with vector column 'embedding'
            supabase.table("embeddings").upsert(data).execute()
        except Exception as e:
            print(f"Error storing embeddings: {e}")
            raise e

    def search(self, query_embedding: List[float], top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[RetrievalResult]:
        """
        Performs a similarity search using pgvector via Supabase RPC.
        """
        try:
            # Call a Postgres function (RPC) that executes the vector similarity search
            # CREATE FUNCTION match_documents (query_embedding vector(1536), match_threshold float, match_count int) ...
            
            params = {
                "query_embedding": query_embedding,
                "match_threshold": 0.5, # Configurable
                "match_count": top_k
            }
            
            # If filters are supported by the RPC, add them
            if filters:
                params["filter"] = filters

            response = supabase.rpc("match_documents", params).execute()
            
            results = []
            for item in response.data:
                results.append(RetrievalResult(
                    chunk_text=item["chunk_text"],
                    similarity=item["similarity"]
                ))
            return results

        except Exception as e:
            print(f"Error searching vectors: {e}")
            return []

    def delete_by_source(self, source: str):
        """
        Deletes all embeddings associated with a specific source.
        """
        try:
            supabase.table("embeddings").delete().eq("source", source).execute()
        except Exception as e:
            print(f"Error deleting embeddings for source {source}: {e}")
            raise e
