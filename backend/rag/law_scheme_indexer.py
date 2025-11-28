from typing import List
from backend.rag.chunker import TextChunker
from backend.rag.embedder import Embedder
from backend.rag.vector_store import VectorStore
from backend.crawlers.gst_crawler import GSTCrawler
from backend.crawlers.income_tax_crawler import IncomeTaxCrawler
from backend.models.rag_models import EmbeddingChunk
# Import other crawlers as needed

class LawSchemeIndexer:
    """
    Orchestrates crawling, chunking, embedding, and storing law/scheme documents into pgvector.
    """

    def __init__(self):
        self.chunker = TextChunker()
        self.embedder = Embedder()
        self.vector_store = VectorStore()
        
        # Initialize crawlers
        self.gst_crawler = GSTCrawler()
        self.it_crawler = IncomeTaxCrawler()

    def index_gst_data(self):
        """
        Crawls, chunks, embeds, and indexes GST data.
        """
        print("Indexing GST data...")
        # 1. Crawl
        chunks = self.gst_crawler.run_full_crawl()
        # 2. Process and Store
        self._process_and_store(chunks)

    def index_income_tax_data(self):
        """
        Crawls, chunks, embeds, and indexes Income Tax data.
        """
        print("Indexing Income Tax data...")
        chunks = self.it_crawler.run_full_crawl()
        self._process_and_store(chunks)

    def _process_and_store(self, chunks: List[EmbeddingChunk]):
        """
        Helper to embed and store chunks.
        """
        if not chunks:
            print("No chunks to process.")
            return

        print(f"Embedding {len(chunks)} chunks...")
        # 3. Embed
        embedded_chunks = self.embedder.embed_chunks(chunks)
        
        print(f"Storing {len(embedded_chunks)} chunks to vector store...")
        # 4. Store
        self.vector_store.store_embeddings(embedded_chunks)
        print("Indexing complete.")

    def run_full_indexing(self):
        """
        Runs indexing for all configured sources.
        """
        self.index_gst_data()
        self.index_income_tax_data()
        # Add other index calls here
