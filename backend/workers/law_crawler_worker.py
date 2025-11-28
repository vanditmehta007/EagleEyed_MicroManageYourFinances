import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime

from backend.crawlers.gst_crawler import GSTCrawler
from backend.crawlers.income_tax_crawler import IncomeTaxCrawler
from backend.crawlers.companies_act_crawler import CompaniesActCrawler
from backend.crawlers.rbi_crawler import RBICrawler
from backend.crawlers.fema_crawler import FEMACrawler
from backend.crawlers.msme_crawler import MSMECrawler
from backend.crawlers.epf_esic_crawler import EPFESICCrawler
from backend.crawlers.icai_guidance_crawler import ICAIGuidanceCrawler
from backend.crawlers.govt_schemes_crawler import GovtSchemesCrawler

from backend.workers.embedding_worker import EmbeddingWorker
from backend.models.rag_models import EmbeddingChunk

# Configure logging
logger = logging.getLogger(__name__)

class LawCrawlerWorker:
    """
    Worker responsible for running various law crawlers and forwarding the data
    to the EmbeddingWorker for RAG indexing.
    """

    def __init__(self):
        self.embedding_worker = EmbeddingWorker()
        
        # Initialize crawlers
        self.crawlers = {
            "gst": GSTCrawler(),
            "income_tax": IncomeTaxCrawler(),
            "companies_act": CompaniesActCrawler(),
            "rbi": RBICrawler(),
            "fema": FEMACrawler(),
            "msme": MSMECrawler(),
            "epf_esic": EPFESICCrawler(),
            "icai": ICAIGuidanceCrawler(),
            "govt_schemes": GovtSchemesCrawler(),
        }

    async def run_crawler(self, crawler_name: str) -> Dict[str, Any]:
        """
        Run a specific crawler by name and index the results.
        
        Args:
            crawler_name: The key of the crawler to run (e.g., "gst", "income_tax").
            
        Returns:
            Status summary.
        """
        crawler = self.crawlers.get(crawler_name)
        if not crawler:
            logger.error(f"Crawler '{crawler_name}' not found.")
            return {"status": "error", "message": f"Crawler '{crawler_name}' not found."}

        try:
            logger.info(f"Starting crawler: {crawler_name}")
            
            # 1. Run the crawl
            # Assuming all crawlers have a `run_full_crawl` method returning List[EmbeddingChunk]
            # or similar text content. 
            # Based on GSTCrawler inspection, it returns List[EmbeddingChunk].
            # However, EmbeddingWorker expects raw text or pre-chunked data.
            # EmbeddingWorker.process_document_content takes text.
            # But GSTCrawler returns chunks.
            # We need to adapt.
            
            # If the crawler returns chunks directly, we can skip the chunking step in EmbeddingWorker
            # and go straight to embedding generation.
            # But EmbeddingWorker is designed to take text.
            # Let's check EmbeddingWorker again.
            # It has `process_document_content(content, source)` -> chunks -> embed -> store.
            
            # If the crawler already returns chunks, we should probably have a method in EmbeddingWorker
            # to process pre-existing chunks.
            # Since I cannot modify EmbeddingWorker right now (I just wrote it), I will adapt here.
            # Or I can use `embedding_worker.vector_store` and `embedding_worker.embedding_service` directly
            # if I had access, but `EmbeddingWorker` encapsulates them.
            
            # Actually, looking at the previous turn, `EmbeddingWorker` has:
            # self.embedding_service = EmbeddingService()
            # self.vector_store = VectorStore()
            # So I can access them if I really need to, or I can reconstruct the flow.
            
            # Ideally, the crawler should return raw text and let the worker chunk it for consistency.
            # But `GSTCrawler` (which I viewed) returns `List[EmbeddingChunk]`.
            # This implies the crawler does the chunking.
            
            # So, the workflow is:
            # 1. Crawler -> List[EmbeddingChunk] (with text, no embedding)
            # 2. Worker -> Generate Embeddings for these chunks
            # 3. Worker -> Store chunks
            
            chunks: List[EmbeddingChunk] = crawler.run_full_crawl()
            
            if not chunks:
                logger.info(f"No data found for {crawler_name}")
                return {"status": "success", "count": 0, "message": "No data found"}

            logger.info(f"Crawler {crawler_name} returned {len(chunks)} chunks.")

            # 2. Generate Embeddings
            # We need to extract text from chunks to pass to embedding service
            chunk_texts = [chunk.chunk_text for chunk in chunks]
            
            # Use the embedding service from the embedding worker
            embeddings = self.embedding_worker.embedding_service.generate_embeddings_batch(chunk_texts)
            
            if len(embeddings) != len(chunks):
                raise ValueError("Mismatch between chunks and embeddings count")
                
            # Assign embeddings
            for i, chunk in enumerate(chunks):
                chunk.embedding = embeddings[i]
                
            # 3. Store
            self.embedding_worker.vector_store.store_embeddings(chunks)
            
            logger.info(f"Successfully indexed {len(chunks)} chunks for {crawler_name}")
            
            return {
                "status": "success",
                "crawler": crawler_name,
                "chunks_indexed": len(chunks),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error running crawler {crawler_name}: {str(e)}")
            return {
                "status": "error",
                "crawler": crawler_name,
                "message": str(e)
            }

    async def run_all_crawlers(self) -> Dict[str, Any]:
        """
        Run all registered crawlers sequentially (or in parallel).
        """
        results = {}
        for name in self.crawlers:
            results[name] = await self.run_crawler(name)
        return results
