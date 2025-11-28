from typing import List
from pydantic import BaseModel

class EmbeddingChunk(BaseModel):
    id: str
    source: str          # "gst_act", "it_act", "companies_act", etc.
    chunk_text: str
    embedding: List[float]

class RetrievalResult(BaseModel):
    chunk_text: str
    similarity: float