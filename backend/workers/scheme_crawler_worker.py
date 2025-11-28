import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from backend.crawlers.govt_schemes_crawler import GovtSchemesCrawler
from backend.workers.embedding_worker import EmbeddingWorker
from backend.models.rag_models import EmbeddingChunk

# Configure logging
logger = logging.getLogger(__name__)

class SchemeCrawlerWorker:
    """
    Worker responsible for crawling government schemes, subsidies, and investment-related notifications.
    It uses the GovtSchemesCrawler to fetch data and the EmbeddingWorker to index it for RAG.
    """

    def __init__(self):
        self.embedding_worker = EmbeddingWorker()
        self.scheme_crawler = GovtSchemesCrawler()

    async def run_scheme_crawl(self) -> Dict[str, Any]:
        """
        Run the government schemes crawler and index the results.
        
        Returns:
            Status summary.
        """
        crawler_name = "govt_schemes"
        try:
            logger.info(f"Starting crawler: {crawler_name}")
            
            # 1. Run the crawl
            chunks: List[EmbeddingChunk] = self.scheme_crawler.run_full_crawl()
            
            if not chunks:
                logger.info(f"No data found for {crawler_name}")
                return {"status": "success", "count": 0, "message": "No data found"}

            logger.info(f"Crawler {crawler_name} returned {len(chunks)} chunks.")

            # 2. Generate Embeddings
            # Extract text from chunks
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

    async def run_specific_category_crawl(self, category: str) -> Dict[str, Any]:
        """
        Run crawl for a specific category of schemes (e.g., 'tax_saving', 'subsidy').
        
        Args:
            category: The category to crawl.
            
        Returns:
            Status summary.
        """
        try:
            logger.info(f"Starting crawl for category: {category}")
            chunks = []
            
            if category == "tax_saving":
                chunks = self.scheme_crawler.crawl_tax_saving_schemes()
            elif category == "investment":
                chunks = self.scheme_crawler.crawl_investment_incentives()
            elif category == "subsidy":
                chunks = self.scheme_crawler.crawl_subsidy_notifications()
            else:
                return {"status": "error", "message": f"Unknown category: {category}"}
                
            if not chunks:
                return {"status": "success", "count": 0, "message": "No data found"}
                
            # Generate Embeddings and Store
            chunk_texts = [chunk.chunk_text for chunk in chunks]
            embeddings = self.embedding_worker.embedding_service.generate_embeddings_batch(chunk_texts)
            
            for i, chunk in enumerate(chunks):
                chunk.embedding = embeddings[i]
                
            self.embedding_worker.vector_store.store_embeddings(chunks)
            
            return {
                "status": "success",
                "category": category,
                "chunks_indexed": len(chunks),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error running category crawl {category}: {str(e)}")
            return {"status": "error", "message": str(e)}
