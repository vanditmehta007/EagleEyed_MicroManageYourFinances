import io
from typing import List, Any, Optional, Tuple, Union
import PyPDF2
import pdfplumber
from pdf2image import convert_from_bytes
from backend.utils.logger import logger

class PDFUtils:
    """
    Helper utilities for processing PDF documents.
    
    Provides functionality for:
    - Extracting text from PDFs
    - Identifying table regions
    - Merging/splitting PDF pages
    - Converting PDF pages to images for OCR
    """

    @staticmethod
    def extract_text(file_content: bytes) -> str:
        """
        Extracts plain text from a PDF file content.
        
        Args:
            file_content: The raw bytes of the PDF file.
            
        Returns:
            Extracted text as a single string.
        """
        try:
            # TODO: Initialize PDF reader (e.g., PyPDF2 or pdfplumber)
            text = ""
            with io.BytesIO(file_content) as f:
                reader = PyPDF2.PdfReader(f)
                
                # TODO: Iterate through pages and extract text
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                        
            # TODO: Return extracted text
            return text.strip()
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            return ""

    @staticmethod
    def extract_tables(file_content: bytes) -> List[List[List[str]]]:
        """
        Extracts tables from a PDF using heuristics or library support.
        
        Args:
            file_content: The raw bytes of the PDF file.
            
        Returns:
            A list of tables, where each table is a list of rows, and each row is a list of cell strings.
        """
        tables = []
        try:
            # TODO: Initialize pdfplumber
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                # TODO: Iterate through pages
                for page in pdf.pages:
                    # TODO: Use extract_table() method
                    # extract_tables returns a list of tables for the page
                    page_tables = page.extract_tables()
                    
                    # TODO: Clean and normalize table data
                    for table in page_tables:
                        # Filter out empty rows or very small tables
                        if table and len(table) > 1:
                            cleaned_table = [
                                [str(cell).strip() if cell else "" for cell in row]
                                for row in table
                            ]
                            tables.append(cleaned_table)
                            
            # TODO: Return list of extracted tables
            return tables
        except Exception as e:
            logger.error(f"Failed to extract tables from PDF: {e}")
            return []

    @staticmethod
    def get_page_count(file_content: bytes) -> int:
        """
        Returns the number of pages in the PDF.
        
        Args:
            file_content: The raw bytes of the PDF file.
            
        Returns:
            Number of pages.
        """
        try:
            # TODO: Initialize PDF reader
            with io.BytesIO(file_content) as f:
                reader = PyPDF2.PdfReader(f)
                # TODO: Return len(reader.pages)
                return len(reader.pages)
        except Exception as e:
            logger.error(f"Failed to get page count: {e}")
            return 0

    @staticmethod
    def merge_pdfs(pdf_files: List[bytes]) -> bytes:
        """
        Merges multiple PDF files into a single PDF.
        
        Args:
            pdf_files: List of PDF file bytes.
            
        Returns:
            Bytes of the merged PDF.
        """
        try:
            # TODO: Initialize PDF merger
            merger = PyPDF2.PdfMerger()
            
            # TODO: Append each PDF file
            for pdf_bytes in pdf_files:
                merger.append(io.BytesIO(pdf_bytes))
            
            # TODO: Write to output stream
            output_stream = io.BytesIO()
            merger.write(output_stream)
            
            # TODO: Return output bytes
            return output_stream.getvalue()
        except Exception as e:
            logger.error(f"Failed to merge PDFs: {e}")
            return b""

    @staticmethod
    def split_pdf(file_content: bytes, page_range: Tuple[int, int]) -> bytes:
        """
        Extracts a range of pages from a PDF.
        
        Args:
            file_content: The raw bytes of the PDF file.
            page_range: Tuple (start_page, end_page) 0-indexed, inclusive.
            
        Returns:
            Bytes of the new PDF containing only the selected pages.
        """
        try:
            # TODO: Initialize PDF reader and writer
            reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            writer = PyPDF2.PdfWriter()
            
            start, end = page_range
            total_pages = len(reader.pages)
            
            # Validate range
            start = max(0, start)
            end = min(total_pages - 1, end)
            
            if start > end:
                return b""
            
            # TODO: Iterate through specified page range
            # TODO: Add pages to writer
            for i in range(start, end + 1):
                writer.add_page(reader.pages[i])
            
            # TODO: Write to output stream
            output_stream = io.BytesIO()
            writer.write(output_stream)
            
            # TODO: Return output bytes
            return output_stream.getvalue()
        except Exception as e:
            logger.error(f"Failed to split PDF: {e}")
            return b""

    @staticmethod
    def convert_to_images(file_content: bytes, dpi: int = 300) -> List[Any]:
        """
        Converts PDF pages to images (e.g., for OCR).
        
        Args:
            file_content: The raw bytes of the PDF file.
            dpi: Resolution for the output images.
            
        Returns:
            List of image objects (e.g., PIL Images).
        """
        try:
            # TODO: Use pdf2image or similar library
            # TODO: Convert pages to images
            images = convert_from_bytes(file_content, dpi=dpi)
            
            # TODO: Return list of images
            return images
        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {e}")
            return []

    @staticmethod
    def is_searchable_pdf(file_content: bytes) -> bool:
        """
        Checks if the PDF contains extractable text (is searchable).
        
        Args:
            file_content: The raw bytes of the PDF file.
            
        Returns:
            True if text can be extracted, False if it's likely a scanned image.
        """
        try:
            # TODO: Try extracting text from a few pages
            text = PDFUtils.extract_text(file_content)
            
            # TODO: If significant text found, return True
            # Heuristic: If we find more than 50 characters, it's likely searchable
            if len(text.strip()) > 50:
                return True
                
            # TODO: Otherwise return False
            return False
        except Exception:
            return False
