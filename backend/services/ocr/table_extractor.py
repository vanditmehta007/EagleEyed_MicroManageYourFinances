from typing import List, Dict, Any, Optional
import io
# import camelot # Uncomment when installed
# import tabula # Uncomment when installed
# import pdfplumber # Uncomment when installed
from backend.utils.logger import logger
from backend.utils.pdf_utils import PDFUtils

class TableExtractor:
    """
    Service for extracting structured tables from PDFs.
    
    Strategies:
    1. Lattice/Stream extraction (Camelot/Tabula) for native PDFs.
    2. Visual extraction (pdfplumber) for line-based tables.
    3. Fallback to OCR (via external service) for scanned images.
    """

    def extract_tables(self, file_content: bytes, strategy: str = "auto") -> List[Dict[str, Any]]:
        """
        Extract tables from PDF content.
        
        Args:
            file_content: Raw PDF bytes.
            strategy: Extraction strategy ('auto', 'lattice', 'stream', 'ocr').
            
        Returns:
            List of dictionaries representing tables.
            Each dict contains: 'page', 'bbox', 'data' (List[List[str]]).
        """
        logger.info(f"Starting table extraction with strategy: {strategy}")
        
        tables = []
        
        # 1. Check if PDF is text-based (searchable)
        is_searchable = PDFUtils.is_searchable_pdf(file_content)
        
        if not is_searchable or strategy == "ocr":
            logger.info("PDF is scanned or OCR strategy requested. Using OCR fallback.")
            return self._extract_with_ocr(file_content)

        # 2. Try Camelot/Tabula (Lattice for bordered, Stream for borderless)
        try:
            # Placeholder for Camelot/Tabula logic
            # tables = self._extract_with_camelot(file_content)
            # if not tables:
            #     tables = self._extract_with_tabula(file_content)
            pass
        except Exception as e:
            logger.warning(f"Camelot/Tabula extraction failed: {e}")

        # 3. Fallback to pdfplumber if no tables found yet
        if not tables:
            logger.info("Falling back to pdfplumber.")
            try:
                tables = self._extract_with_pdfplumber(file_content)
            except Exception as e:
                logger.error(f"pdfplumber extraction failed: {e}")

        return self._normalize_output(tables)

    def _extract_with_camelot(self, file_content: bytes) -> List[Any]:
        """
        Extract using Camelot (good for complex layouts).
        """
        # TODO: Save bytes to temp file (Camelot needs path)
        # TODO: camelot.read_pdf(path, flavor='lattice'/'stream')
        # TODO: Return raw table objects
        return []

    def _extract_with_tabula(self, file_content: bytes) -> List[Any]:
        """
        Extract using Tabula (Java-based, robust).
        """
        # TODO: tabula.read_pdf(io.BytesIO(file_content), pages='all')
        return []

    def _extract_with_pdfplumber(self, file_content: bytes) -> List[Dict[str, Any]]:
        """
        Extract using pdfplumber (visual line detection).
        """
        extracted = []
        # TODO: with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        # TODO:     for page in pdf.pages:
        # TODO:         tables = page.extract_tables()
        # TODO:         for table in tables:
        # TODO:             extracted.append({"page": page.page_number, "data": table})
        return extracted

    def _extract_with_ocr(self, file_content: bytes) -> List[Dict[str, Any]]:
        """
        Fallback extraction using OCR (e.g., AWS Textract, Google Vision).
        This would typically call an external OCR service wrapper.
        """
        # TODO: Convert PDF pages to images
        # TODO: Call OCR service (e.g., Textract AnalyzeDocument)
        # TODO: Parse OCR response into table structure
        return []

    def _normalize_output(self, raw_tables: List[Any]) -> List[Dict[str, Any]]:
        """
        Normalize various library outputs into a standard format.
        
        Standard Format:
        [
            {
                "page": 1,
                "bbox": [x1, y1, x2, y2], # Optional
                "data": [
                    ["Header1", "Header2"],
                    ["Row1Col1", "Row1Col2"]
                ]
            },
            ...
        ]
        """
        normalized = []
        for table in raw_tables:
            # Logic to adapt specific library objects to dict
            # For now, assuming raw_tables is already close to dict or list
            if isinstance(table, dict):
                normalized.append(table)
            # Add adapters for Camelot/Tabula objects here
            
        return normalized
