import requests
import uuid
from typing import List, Optional
from bs4 import BeautifulSoup
from backend.models.rag_models import EmbeddingChunk
from backend.utils.logger import logger

class RBICrawler:
    """
    Crawler for fetching RBI Master Circulars, Notifications, and Banking Guidelines.
    Chunks content for RAG ingestion.
    """
    
    BASE_URL = "https://www.rbi.org.in"

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

    def crawl_master_circulars(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks RBI Master Circulars.
        """
        logger.info("Starting crawl for RBI Master Circulars...")
        url = f"{self.BASE_URL}/Scripts/BS_ViewMasterCirculardetails.aspx"
        html = self.fetch_content(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        chunks = []
        
        # Placeholder extraction logic
        content_div = soup.find('div', {'id': 'content'}) 
        if content_div:
            text = content_div.get_text(separator="\n", strip=True)
            chunks.extend(self.chunk_text(text, source="rbi_master_circular"))

        return chunks

    def crawl_notifications(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks RBI Notifications.
        """
        logger.info("Starting crawl for RBI Notifications...")
        url = f"{self.BASE_URL}/Scripts/BS_ViewNotification.aspx"
        html = self.fetch_content(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        chunks = []
        
        # Extraction logic
        return chunks

    def crawl_guidelines(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks Banking Guidelines.
        """
        logger.info("Starting crawl for RBI Guidelines...")
        url = f"{self.BASE_URL}/Scripts/BS_ViewGuidelines.aspx" # Hypothetical URL
        html = self.fetch_content(url)
        if not html:
            return []
            
        chunks = []
        # Extraction logic
        return chunks

    def run_full_crawl(self) -> List[EmbeddingChunk]:
        """
        Executes all crawl functions and returns aggregated chunks.
        """
        all_chunks = []
        all_chunks.extend(self.crawl_master_circulars())
        all_chunks.extend(self.crawl_notifications())
        all_chunks.extend(self.crawl_guidelines())
        
        logger.info(f"Completed RBI crawl. Generated {len(all_chunks)} chunks.")
        return all_chunks
