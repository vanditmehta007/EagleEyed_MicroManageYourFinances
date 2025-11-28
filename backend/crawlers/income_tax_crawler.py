import requests
import uuid
from typing import List, Optional
from bs4 import BeautifulSoup
from backend.models.rag_models import EmbeddingChunk
from backend.utils.logger import logger

class IncomeTaxCrawler:
    """
    Crawler for fetching Income Tax Act sections, rules, notifications, TDS/TCS circulars, and case law summaries.
    Chunks content for RAG ingestion.
    """
    
    BASE_URL = "https://incometaxindia.gov.in" 

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

    def crawl_act_sections(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks Income Tax Act Sections.
        """
        logger.info("Starting crawl for Income Tax Act Sections...")
        url = f"{self.BASE_URL}/pages/acts/income-tax-act.aspx"
        html = self.fetch_content(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        chunks = []
        
        # Placeholder extraction logic
        content_div = soup.find('div', {'id': 'content'}) # Generic ID
        if content_div:
            text = content_div.get_text(separator="\n", strip=True)
            chunks.extend(self.chunk_text(text, source="it_act_section"))

        return chunks

    def crawl_rules(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks Income Tax Rules.
        """
        logger.info("Starting crawl for Income Tax Rules...")
        url = f"{self.BASE_URL}/pages/rules/income-tax-rules-1962.aspx"
        html = self.fetch_content(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        chunks = []
        
        content_div = soup.find('div', {'id': 'content'})
        if content_div:
            text = content_div.get_text(separator="\n", strip=True)
            chunks.extend(self.chunk_text(text, source="it_rules"))
            
        return chunks

    def crawl_notifications(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks Income Tax Notifications.
        """
        logger.info("Starting crawl for Income Tax Notifications...")
        url = f"{self.BASE_URL}/pages/communications/notifications.aspx"
        html = self.fetch_content(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        chunks = []
        
        # Logic to iterate through notification list/table
        
        return chunks

    def crawl_circulars(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks TDS/TCS Circulars.
        """
        logger.info("Starting crawl for Income Tax Circulars...")
        url = f"{self.BASE_URL}/pages/communications/circulars.aspx"
        html = self.fetch_content(url)
        if not html:
            return []
            
        chunks = []
        # Extraction logic
        return chunks

    def crawl_case_laws(self) -> List[EmbeddingChunk]:
        """
        Fetches and chunks Case Law Summaries.
        """
        logger.info("Starting crawl for Case Law Summaries...")
        # Note: Case laws might come from a different section or external source
        url = f"{self.BASE_URL}/pages/judicial-updates.aspx" 
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
        all_chunks.extend(self.crawl_act_sections())
        all_chunks.extend(self.crawl_rules())
        all_chunks.extend(self.crawl_notifications())
        all_chunks.extend(self.crawl_circulars())
        all_chunks.extend(self.crawl_case_laws())
        
        logger.info(f"Completed Income Tax crawl. Generated {len(all_chunks)} chunks.")
        return all_chunks
