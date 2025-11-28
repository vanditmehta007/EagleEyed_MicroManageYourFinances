from typing import List
import os
# import openai
from backend.models.rag_models import EmbeddingChunk

class Embedder:
    """
    Converts text chunks into vector embeddings.
    Default implementation assumes OpenAI embeddings, but can be swapped.
    """

    def __init__(self):
        # self.api_key = os.environ.get("OPENAI_API_KEY")
        # openai.api_key = self.api_key
        pass

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a vector embedding for a single string of text.
        """
        # Placeholder for actual API call
        # response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
        # return response['data'][0]['embedding']
        
        # Return a dummy vector of length 1536 (common for OpenAI) for testing
        return [0.0] * 1536

    def embed_chunks(self, chunks: List[EmbeddingChunk]) -> List[EmbeddingChunk]:
        """
        Generates embeddings for a list of chunks and updates them in place.
        """
        for chunk in chunks:
            chunk.embedding = self.generate_embedding(chunk.chunk_text)
        return chunks
