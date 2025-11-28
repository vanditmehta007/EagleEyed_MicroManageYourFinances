import requests
import uuid
from typing import List, Optional
from bs4 import BeautifulSoup
from backend.models.rag_models import EmbeddingChunk
from backend.utils.logger import logger

class EPFESICCrawler:
    """
    Crawler for fetching EPF and ESIC contribution rules, wage ceilings, notifications, and compliance circulars.
    Chunks content for RAG ingestion.
    """
    
    EPF_BASE_URL = "https://www.epfindia.gov.in"
    ESIC_BASE_URL = "https://www.esic.nic.in"

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

    def crawl_epf_rules(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks EPF Rules and Schemes.
        """
        logger.info("Starting crawl for EPF Rules...")
        url = f"{self.EPF_BASE_URL}/site_en/Rules_Regulations.php" # Hypothetical URL
        html = self.fetch_content(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        chunks = []
        
        # Placeholder extraction logic
        content_div = soup.find('div', {'id': 'content'}) 
        if content_div:
            text = content_div.get_text(separator="\n", strip=True)
            chunks.extend(self.chunk_text(text, source="epf_rules"))

        return chunks

    def crawl_esic_rules(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks ESIC Rules and Regulations.
        """
        logger.info("Starting crawl for ESIC Rules...")
        url = f"{self.ESIC_BASE_URL}/rules-regulations" # Hypothetical URL
        html = self.fetch_content(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        chunks = []
        
        # Extraction logic
        return chunks

    def crawl_wage_ceilings(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks Wage Ceiling information.
        """
        logger.info("Starting crawl for Wage Ceilings...")
        # This might be part of FAQs or specific notifications
        chunks = []
        # Placeholder for manual or scraped data
        text = "EPF Wage Ceiling: Rs. 15,000 per month. ESIC Wage Ceiling: Rs. 21,000 per month."
        chunks.extend(self.chunk_text(text, source="wage_ceilings"))
        return chunks

    def crawl_notifications(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks EPF/ESIC Notifications.
        """
        logger.info("Starting crawl for EPF/ESIC Notifications...")
        # EPF Notifications
        epf_url = f"{self.EPF_BASE_URL}/site_en/Circulars.php"
        # ESIC Notifications
        esic_url = f"{self.ESIC_BASE_URL}/circulars"
        
        chunks = []
        # Logic to fetch and parse both
        return chunks

    def crawl_circulars(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks Compliance Circulars.
        """
        logger.info("Starting crawl for Compliance Circulars...")
        # Often same as notifications page
        return []

    def run_full_crawl(self) -> List[EmbeddingChunk]:
        """
        Executes all crawl functions and returns aggregated chunks.
        """
        all_chunks = []
        all_chunks.extend(self.crawl_epf_rules())
        all_chunks.extend(self.crawl_esic_rules())
        all_chunks.extend(self.crawl_wage_ceilings())
        all_chunks.extend(self.crawl_notifications())
        all_chunks.extend(self.crawl_circulars())
        
        logger.info(f"Completed EPF/ESIC crawl. Generated {len(all_chunks)} chunks.")
        return all_chunks
