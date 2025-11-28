import uuid
import os
import json
from typing import List, Dict, Any
from backend.models.rag_models import EmbeddingChunk
from backend.utils.file_utils import FileUtils
from backend.utils.pdf_utils import PDFUtils
from backend.utils.logger import logger

class TextChunker:
    """
    Splits law, scheme, and compliance documents into RAG-ready chunks with metadata.
    """

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, source: str, metadata: Dict[str, Any] = None) -> List[EmbeddingChunk]:
        """
        Splits plain text into overlapping chunks.
        
        Args:
            text: The full text content to chunk.
            source: The source identifier (e.g., 'gst_act', 'it_act').
            metadata: Additional metadata to attach to each chunk.
            
        Returns:
            List of EmbeddingChunk objects.
        """
        if metadata is None:
            metadata = {}

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk_content = text[start:end]
            
            # TODO: Implement smarter splitting (e.g., by paragraph or sentence) if needed
            
            chunk = EmbeddingChunk(
                id=str(uuid.uuid4()),
                source=source,
                chunk_text=chunk_content,
                embedding=[] # Embedding will be generated later
            )
            # TODO: Attach metadata to chunk if model supports it (currently EmbeddingChunk only has source)
            
            chunks.append(chunk)
            
            # Move start forward by chunk_size - overlap
            start += (self.chunk_size - self.overlap)
            
            # Prevent infinite loop if overlap >= chunk_size (though init should prevent this)
            if self.overlap >= self.chunk_size:
                start += 1 

        return chunks

    def chunk_document(self, file_path: str, source: str) -> List[EmbeddingChunk]:
        """
        Reads a file and chunks its content.
        
        Args:
            file_path: Path to the file.
            source: Source identifier.
            
        Returns:
            List of EmbeddingChunk objects.
        """
        # Validate file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return []
        
        # Get file extension
        file_ext = FileUtils.get_file_extension(file_path)
        text = ""
        
        try:
            # Handle different file types
            if file_ext in ['txt', 'md', 'csv', 'html']:
                # Read plain text files
                content = FileUtils.read_file(file_path, mode='r')
                if content:
                    text = content
                else:
                    logger.warning(f"Failed to read text file: {file_path}")
                    
            elif file_ext == 'pdf':
                # Read PDF files
                pdf_bytes = FileUtils.read_file(file_path, mode='rb')
                if pdf_bytes:
                    # Extract text from PDF
                    text = PDFUtils.extract_text(pdf_bytes)
                    if not text:
                        logger.warning(f"No text extracted from PDF: {file_path}")
                else:
                    logger.warning(f"Failed to read PDF file: {file_path}")
                    
            elif file_ext == 'json':
                # Read JSON files and convert to text
                content = FileUtils.read_file(file_path, mode='r')
                if content:
                    try:
                        json_data = json.loads(content)
                        # Convert JSON to formatted string for chunking
                        text = json.dumps(json_data, indent=2)
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in file {file_path}: {e}")
                        text = content  # Fall back to raw content
                else:
                    logger.warning(f"Failed to read JSON file: {file_path}")
                    
            else:
                # Unsupported file type - try reading as text
                logger.warning(f"Unsupported file type '{file_ext}' for {file_path}, attempting text read")
                content = FileUtils.read_file(file_path, mode='r')
                if content:
                    text = content
                else:
                    logger.error(f"Could not read file: {file_path}")
                    
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return []
        
        # Chunk the extracted text
        if text:
            return self.chunk_text(text, source)
        else:
            logger.warning(f"No text content extracted from {file_path}")
            return []

