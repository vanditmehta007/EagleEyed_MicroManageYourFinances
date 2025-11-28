import requests
import uuid
from typing import List, Optional
from bs4 import BeautifulSoup
from backend.models.rag_models import EmbeddingChunk
from backend.utils.logger import logger

class MSMECrawler:
    """
    Crawler for fetching MSME Act rules, payment timeline obligations, interest penalty clauses, and government notifications.
    Chunks content for RAG ingestion.
    """
    
    BASE_URL = "https://msme.gov.in"

    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def fetch_content(self, url: str) -> Optional[str]:
        """Fetches HTML content from a URL."""
        try:
            response = self.session.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch URL {url}: {str(e)}")
            return None

    def chunk_text(self, text: str, source: str, chunk_size: int = 1000, overlap: int = 200) -> List[EmbeddingChunk]:
        """
        Splits text into overlapping chunks for RAG.
        """
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size
            chunk_content = text[start:end]
            
            chunk = EmbeddingChunk(
                id=str(uuid.uuid4()),
                source=source,
                chunk_text=chunk_content,
                embedding=[] 
            )
            chunks.append(chunk)
            
            start += (chunk_size - overlap)
        
        return chunks

    def crawl_act_rules(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks MSME Act and Rules.
        """
        logger.info("Starting crawl for MSME Act & Rules...")
        url = f"{self.BASE_URL}/documents/acts-and-rules"
        html = self.fetch_content(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        chunks = []
        
        # Placeholder extraction logic
        content_div = soup.find('div', {'id': 'content'}) 
        if content_div:
            text = content_div.get_text(separator="\n", strip=True)
            chunks.extend(self.chunk_text(text, source="msme_act_rules"))

        return chunks

    def crawl_payment_obligations(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks Payment Timeline Obligations (Section 15).
        """
        logger.info("Starting crawl for MSME Payment Obligations...")
        # Specific URL or extraction from Act
        # Placeholder logic
        chunks = []
        # Simulate fetching specific section text
        text = "Where any supplier supplies any goods or renders any services to any buyer, the buyer shall make payment therefor on or before the date agreed upon between him and the supplier in writing or, where there is no agreement in this behalf, before the appointed day..."
        chunks.extend(self.chunk_text(text, source="msme_payment_obligations"))
        return chunks

    def crawl_interest_penalties(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks Interest Penalty Clauses (Section 16).
        """
        logger.info("Starting crawl for MSME Interest Penalties...")
        # Specific URL or extraction from Act
        chunks = []
        # Simulate fetching specific section text
        text = "Where any buyer fails to make payment of the amount to the supplier, as required under section 15, the buyer shall, notwithstanding anything contained in any agreement between the buyer and the supplier or in any law for the time being in force, be liable to pay compound interest with monthly rests to the supplier..."
        chunks.extend(self.chunk_text(text, source="msme_interest_penalties"))
        return chunks

    def crawl_notifications(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks MSME Notifications.
        """
        logger.info("Starting crawl for MSME Notifications...")
        url = f"{self.BASE_URL}/documents/notifications"
        html = self.fetch_content(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        chunks = []
        
        # Extraction logic
        return chunks

    def run_full_crawl(self) -> List[EmbeddingChunk]:
        """
        Executes all crawl functions and returns aggregated chunks.
        """
        all_chunks = []
        all_chunks.extend(self.crawl_act_rules())
        all_chunks.extend(self.crawl_payment_obligations())
        all_chunks.extend(self.crawl_interest_penalties())
        all_chunks.extend(self.crawl_notifications())
        
        logger.info(f"Completed MSME crawl. Generated {len(all_chunks)} chunks.")
        return all_chunks
