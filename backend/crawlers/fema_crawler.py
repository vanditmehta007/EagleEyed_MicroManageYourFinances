import requests
import uuid
from typing import List, Optional
from bs4 import BeautifulSoup
from backend.models.rag_models import EmbeddingChunk
from backend.utils.logger import logger

class FEMACrawler:
    """
    Crawler for fetching FEMA Rules, Regulations, Circulars, and Forex Compliance Guidelines.
    Chunks content for RAG ingestion.
    """
    
    BASE_URL = "https://www.rbi.org.in/Scripts/Fema.aspx" # FEMA section on RBI website

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
        Fetches and chunks FEMA Act and Rules.
        """
        logger.info("Starting crawl for FEMA Act & Rules...")
        url = f"{self.BASE_URL}" # Main FEMA page often lists acts/rules
        html = self.fetch_content(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        chunks = []
        
        # Placeholder extraction logic
        content_div = soup.find('div', {'id': 'content'}) 
        if content_div:
            text = content_div.get_text(separator="\n", strip=True)
            chunks.extend(self.chunk_text(text, source="fema_act_rules"))

        return chunks

    def crawl_regulations(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks FEMA Regulations.
        """
        logger.info("Starting crawl for FEMA Regulations...")
        # Specific URL for regulations if available
        url = "https://www.rbi.org.in/Scripts/BS_FemaNotifications.aspx" 
        html = self.fetch_content(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        chunks = []
        
        # Extraction logic
        return chunks

    def crawl_circulars(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks FEMA Circulars/AP DIR Series.
        """
        logger.info("Starting crawl for FEMA Circulars...")
        url = "https://www.rbi.org.in/Scripts/BS_ApCircularsDisplay.aspx"
        html = self.fetch_content(url)
        if not html:
            return []
            
        chunks = []
        # Extraction logic
        return chunks

    def crawl_forex_guidelines(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks Forex Compliance Guidelines.
        """
        logger.info("Starting crawl for Forex Guidelines...")
        # Placeholder URL
        url = "https://www.rbi.org.in/Scripts/BS_ViewMasCirculardetails.aspx?id=9898" # Master Direction - Forex
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
        all_chunks.extend(self.crawl_act_rules())
        all_chunks.extend(self.crawl_regulations())
        all_chunks.extend(self.crawl_circulars())
        all_chunks.extend(self.crawl_forex_guidelines())
        
        logger.info(f"Completed FEMA crawl. Generated {len(all_chunks)} chunks.")
        return all_chunks
