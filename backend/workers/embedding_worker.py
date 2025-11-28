import logging
from typing import List, Dict, Any
from backend.services.rag_service.embedding_service import EmbeddingService
from backend.rag.chunker import TextChunker
from backend.rag.vector_store import VectorStore
from backend.models.rag_models import EmbeddingChunk

# Configure logging
logger = logging.getLogger(__name__)

class EmbeddingWorker:
    """
    Worker responsible for generating embeddings for law/scheme documents.
    It orchestrates chunking, embedding generation, and storage.
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.chunker = TextChunker()
        self.vector_store = VectorStore()

    def process_document_content(self, content: str, source: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process raw text content: chunk it, embed it, and store it.

        Args:
            content: The full text content of the document.
            source: Identifier for the document source (e.g., "gst_act_2017").
            metadata: Optional metadata to associate with the chunks.

        Returns:
            Summary dictionary containing status and count of processed chunks.
        """
        try:
            logger.info(f"Starting embedding generation for source: {source}")

            # 1. Chunk the content
            chunks: List[EmbeddingChunk] = self.chunker.chunk_text(content, source, metadata)
            if not chunks:
                logger.warning(f"No chunks generated for source: {source}")
                return {"status": "warning", "message": "No chunks generated", "count": 0}

            logger.info(f"Generated {len(chunks)} chunks for source: {source}")

            # 2. Generate embeddings in batches
            chunk_texts = [chunk.chunk_text for chunk in chunks]
            
            # Note: Depending on the API limit, we might need to batch this further
            # For now, we assume the service handles batching or the list is reasonable
            embeddings = self.embedding_service.generate_embeddings_batch(chunk_texts)

            if len(embeddings) != len(chunks):
                raise ValueError("Mismatch between number of chunks and generated embeddings")

            # 3. Assign embeddings back to chunks
            for i, chunk in enumerate(chunks):
                chunk.embedding = embeddings[i]

            # 4. Store in Vector Store
            self.vector_store.store_embeddings(chunks)

            logger.info(f"Successfully stored {len(chunks)} embeddings for source: {source}")
            return {
                "status": "success",
                "count": len(chunks),
                "source": source
            }

        except Exception as e:
            logger.error(f"Error processing embeddings for source {source}: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "source": source
            }

    def process_law_update(self, update_text: str, law_id: str) -> Dict[str, Any]:
        """
        Process a specific update to a law.
        
        Args:
            update_text: The text of the amendment or update.
            law_id: The ID of the law being updated.
            
        Returns:
            Status dictionary.
        """
        return self.process_document_content(update_text, source=f"law_update_{law_id}")

    def reindex_source(self, content: str, source: str) -> Dict[str, Any]:
        """
        Re-index a source completely (delete old, insert new).
        
        Args:
            content: New full content.
            source: Source identifier.
            
        Returns:
            Status dictionary.
        """
        try:
            logger.info(f"Re-indexing source: {source}")
            
            # Delete existing
            self.vector_store.delete_by_source(source)
            
            # Process new
            return self.process_document_content(content, source)
            
        except Exception as e:
            logger.error(f"Error re-indexing source {source}: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "source": source
            }
