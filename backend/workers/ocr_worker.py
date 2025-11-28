import logging
import io
from typing import Dict, Any, Optional
from fastapi import UploadFile
from backend.services.ocr.ocr_service import OCRService
from backend.utils.supabase_client import supabase

# Configure logging
logger = logging.getLogger(__name__)

class MockUploadFile:
    """
    Mock class to simulate FastAPI UploadFile for OCR service.
    """
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self.file = io.BytesIO(content)
        self.content_type = "application/octet-stream"

class OCRWorker:
    """
    Worker responsible for processing OCR jobs asynchronously.
    It fetches the document file, runs OCR/Table extraction, and updates the document metadata or returns results.
    """

    def __init__(self):
        self.ocr_service = OCRService()

    async def process_document_ocr(self, document_id: str, extract_tables: bool = False) -> Dict[str, Any]:
        """
        Process a document for OCR.

        Args:
            document_id: The ID of the document in Supabase.
            extract_tables: Whether to attempt table extraction specifically.

        Returns:
            Dictionary with status and extracted content.
        """
        try:
            logger.info(f"Starting OCR processing for document {document_id}")

            # 1. Fetch document metadata to get file path
            try:
                response = supabase.table("documents").select("*").eq("id", document_id).single().execute()
                if not response.data:
                    raise ValueError(f"Document {document_id} not found")
                document = response.data
            except Exception as e:
                logger.error(f"Failed to fetch document metadata: {e}")
                return {"status": "error", "message": str(e)}

            # 2. Download file content
            try:
                file_path = document["file_path"]
                file_content = supabase.storage.from_("documents").download(file_path)
            except Exception as e:
                logger.error(f"Failed to download file {file_path}: {e}")
                return {"status": "error", "message": f"Download failed: {str(e)}"}

            # 3. Prepare Mock File
            mock_file = MockUploadFile(document["original_filename"], file_content)

            # 4. Run OCR
            extracted_text = ""
            extracted_tables = None

            # Text Extraction
            try:
                text_result = self.ocr_service.extract_text(mock_file)
                if text_result.success:
                    extracted_text = text_result.data
                else:
                    logger.warning(f"OCR text extraction returned failure for {document_id}")
            except Exception as e:
                logger.error(f"OCR text extraction failed: {e}")

            # Table Extraction (if requested)
            if extract_tables:
                try:
                    # Reset file pointer for next read
                    mock_file.file.seek(0) 
                    table_result = self.ocr_service.extract_table(mock_file)
                    if table_result.success:
                        extracted_tables = table_result.data
                except Exception as e:
                    logger.error(f"Table extraction failed: {e}")

            # 5. Update Document Metadata (Optional but recommended)
            # We might want to store the extracted text in a 'content' field or 'metadata' json
            try:
                current_metadata = document.get("metadata") or {}
                current_metadata["ocr_extracted"] = True
                current_metadata["ocr_text_preview"] = extracted_text[:200] if extracted_text else ""
                
                supabase.table("documents").update({
                    "metadata": current_metadata
                }).eq("id", document_id).execute()
            except Exception as e:
                logger.warning(f"Failed to update document metadata with OCR status: {e}")

            logger.info(f"Completed OCR for document {document_id}")
            
            return {
                "status": "success",
                "document_id": document_id,
                "text": extracted_text,
                "tables": extracted_tables
            }

        except Exception as e:
            logger.error(f"Unexpected error in OCR worker for {document_id}: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "document_id": document_id
            }
