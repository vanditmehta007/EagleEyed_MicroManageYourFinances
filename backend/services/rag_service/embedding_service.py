# backend/services/rag_service/embedding_service.py

from typing import List
import os
import time
from backend.utils.logger import logger
from backend.config import settings
# import openai  # USER INPUT REQUIRED: Install 'openai' package: pip install openai

class EmbeddingService:
    """
    Service for generating embeddings for text chunks using external embedding APIs.
    """

    def __init__(self) -> None:
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_EMBEDDING_MODEL
        
        if self.api_key:
            # openai.api_key = self.api_key
            logger.info(f"EmbeddingService initialized with model: {self.model}")
        else:
            logger.warning("EmbeddingService initialized WITHOUT API KEY. Embeddings will be zero-vectors.")

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for a single text string.
        """
        if not text:
            return [0.0] * 1536
            
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set. Returning dummy embedding.")
            return [0.0] * 1536

        try:
            # Clean text
            text = text.replace("\n", " ")
            
            # USER INPUT REQUIRED: Uncomment the following lines after installing openai package
            # response = openai.Embedding.create(input=text, model=self.model)
            # return response['data'][0]['embedding']
            
            # Placeholder for now until package is installed and key provided
            return [0.0] * 1536
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return [0.0] * 1536

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.
        """
        if not texts:
            return []
            
        if not self.api_key:
            return [[0.0] * 1536 for _ in texts]

        try:
            cleaned_texts = [t.replace("\n", " ") for t in texts]
            
            # USER INPUT REQUIRED: Uncomment the following lines after installing openai package
            # response = openai.Embedding.create(input=cleaned_texts, model=self.model)
            # return [item['embedding'] for item in response['data']]
            
            return [[0.0] * 1536 for _ in texts]
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [[0.0] * 1536 for _ in texts]

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        """
        if "text-embedding-3-small" in self.model:
            return 1536
        elif "text-embedding-3-large" in self.model:
            return 3072
        elif "ada-002" in self.model:
            return 1536
        else:
            return 1536
