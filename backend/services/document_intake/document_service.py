# backend/services/document_intake/document_service.py

from typing import Any, Dict, List, Optional
from fastapi import UploadFile, HTTPException
import uuid
from datetime import datetime

from backend.models.document_models import Document, DocumentUploadResponse
from backend.services.document_intake.document_classifier import DocumentClassifier
from supabase import create_client
from backend.config import settings
from backend.utils.logger import logger


class DocumentIntakeService:
    """
    High‑level orchestrator for handling incoming documents.

    The service is responsible for:
    - Detecting the document type (bank statement, invoice, GST JSON, etc.).
    - Routing the file to the appropriate parser/processor.
    - Storing the raw file in Supabase storage and creating a DB record.
    - Triggering downstream metadata extraction.
    - Triggering ledger classification for the extracted transactions.
    """

    # Supabase storage bucket name
    STORAGE_BUCKET = "documents"
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024

    def __init__(self) -> None:
        self.classifier = DocumentClassifier()
        # Use Service Role Key to bypass RLS for document ingestion
        self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        logger.info("DocumentIntakeService initialized")

    def detect_type(self, file: UploadFile) -> str:
        """
        Determine the document type based on file name, MIME type, and/or content.
        """
        filename = file.filename.lower() if file.filename else ""
        
        # Check file extension and name patterns
        if filename.endswith('.json'):
            if 'gst' in filename:
                return "gst_json"
            return "json_data"
        
        if filename.endswith('.pdf'):
            if 'bank' in filename or 'statement' in filename:
                return "bank_statement"
            elif 'invoice' in filename or 'bill' in filename:
                return "invoice"
            return "expense_bill"
        
        if filename.endswith(('.xlsx', '.xls', '.csv')):
            if 'bank' in filename:
                return "bank_statement"
            return "transaction_sheet"
        
        # Default
        return "expense"

    def route_to_parser(self, doc_type: str) -> Any:
        """
        Return the parser/processor object that can handle the given document type.
        """
        from backend.services.document_intake.bank_statement_parser import BankStatementParser
        from backend.services.document_intake.invoice_parser import InvoiceParser
        from backend.services.document_intake.gst_json_parser import GSTJSONParser
        
        parser_map = {
            "bank_statement": BankStatementParser(),
            "invoice": InvoiceParser(),
            "gst_json": GSTJSONParser(),
            "expense_bill": InvoiceParser(),  # Reuse invoice parser
            "transaction_sheet": None  # Handled by SheetService
        }
        return parser_map.get(doc_type)

    async def store_document(self, file: UploadFile, doc_type: str, client_id: str, folder_category: str = None) -> Document:
        """
        Upload file to storage and create database record.
        """
        try:
            # Read file content
            content = await file.read()
            
            # Generate unique path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_filename = file.filename.replace(" ", "_")
            file_path = f"{client_id}/{folder_category or 'Uncategorized'}/{timestamp}_{clean_filename}"
            
            # Upload to Supabase Storage
            self.supabase.storage.from_(self.STORAGE_BUCKET).upload(
                path=file_path,
                file=content,
                file_options={"content-type": file.content_type}
            )
            
            # Create DB record
            file_size = len(content)
            
            data = {
                "client_id": client_id,
                "file_path": file_path,
                "file_type": doc_type,
                "original_filename": file.filename,
                "folder_category": folder_category or "Uncategorized",
                "file_size": file_size,
                "metadata": {"content_type": file.content_type}
            }
            
            response = self.supabase.table("documents").insert(data).execute()
            
            if response.data:
                logger.info(f"Document stored successfully: {response.data[0]['id']}")
                return Document(**response.data[0])
            else:
                raise Exception("Failed to insert document record")
                
        except Exception as e:
            logger.error(f"Failed to store document: {e}")
            raise e

    def trigger_metadata_extraction(self, document_id: str) -> None:
        """
        Trigger the metadata extraction process.
        """
        logger.info(f"Metadata extraction triggered for document {document_id}")
        # Placeholder for actual extraction logic
        pass

    def trigger_ledger_classification(self, document_id: str) -> None:
        """
        After metadata extraction, start ledger classification for the resulting transactions.
        """
        logger.info(f"Ledger classification triggered for document {document_id}")
        # TODO: Enqueue classification job
        # This would typically:
        # 1. Wait for metadata extraction to complete
        # 2. Fetch extracted transactions
        # 3. Run AI/ML classification on each transaction
        # 4. Update transaction records with classified ledger accounts

    async def upload_document(self, file: UploadFile, client_id: str, folder_category: str = None) -> DocumentUploadResponse:
        """
        Upload a document for processing.
        Main entry point for document upload.
        """
        try:
            # Validate file
            if not file.filename:
                raise HTTPException(status_code=400, detail="Filename is required")
            
            logger.info(f"Processing document upload: {file.filename} for client {client_id}")
            
            # Detect document type
            doc_type = self.detect_type(file)
            logger.info(f"Detected document type: {doc_type}")
            
            # Reset file pointer after classification
            await file.seek(0)
            
            # Store document (uploads to storage and creates DB record)
            document = await self.store_document(file, doc_type, client_id, folder_category)
            
            # Trigger background processing
            self.trigger_metadata_extraction(document.id)
            self.trigger_ledger_classification(document.id)
            
            return DocumentUploadResponse(
                id=document.id,
                file_path=document.file_path,
                file_type=document.file_type
            )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Document upload failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

    def list_documents(self, client_id: str, folder_category: str = None, limit: int = 100, offset: int = 0) -> List[Document]:
        """
        List documents for a client with pagination.
        """
        try:
            query = self.supabase.table("documents").select("*").eq("client_id", client_id).is_("deleted_at", "null")
            
            if folder_category:
                query = query.eq("folder_category", folder_category)
            
            # Add pagination
            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
            
            response = query.execute()
            docs = response.data if response.data else []
            
            logger.info(f"Retrieved {len(docs)} documents for client {client_id}")
            return [Document(**doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []

    def get_document(self, document_id: str) -> Document:
        """
        Get document metadata.
        """
        try:
            response = self.supabase.table("documents").select("*").eq("id", document_id).single().execute()
            
            if response.data:
                return Document(**response.data)
            else:
                raise HTTPException(status_code=404, detail="Document not found")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")

    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Soft delete a document.
        """
        try:
            response = self.supabase.table("documents").update({
                "deleted_at": datetime.utcnow().isoformat()
            }).eq("id", document_id).execute()
            
            return {"success": True, "message": "Document deleted"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def restore_document(self, document_id: str) -> Document:
        """
        Restore a soft-deleted document.
        """
        try:
            response = self.supabase.table("documents").update({
                "deleted_at": None,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", document_id).execute()
            
            if response.data:
                logger.info(f"Document restored: {document_id}")
                return Document(**response.data[0])
            else:
                raise HTTPException(status_code=404, detail="Document not found")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to restore document: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to restore document: {str(e)}")
    
    async def download_document(self, document_id: str) -> bytes:
        """
        Download document file from storage.
        """
        try:
            # Get document metadata
            document = self.get_document(document_id)
            
            # Download from storage
            file_data = self.supabase.storage.from_(self.STORAGE_BUCKET).download(document.file_path)
            
            logger.info(f"Downloaded document: {document_id}")
            return file_data
            
        except Exception as e:
            logger.error(f"Failed to download document: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to download document: {str(e)}")

    def get_signed_url(self, document_id: str, expires_in: int = 3600) -> str:
        """
        Get a signed URL for viewing the document.
        """
        try:
            # Get document metadata
            document = self.get_document(document_id)
            
            # Create signed URL
            response = self.supabase.storage.from_(self.STORAGE_BUCKET).create_signed_url(
                document.file_path, 
                expires_in
            )
            
            if response:
                # Supabase-py v2 returns a dict or string depending on version, handle both
                if isinstance(response, dict) and 'signedURL' in response:
                    return response['signedURL']
                elif isinstance(response, str):
                    return response
                # Fallback for some versions
                return response['signedURL'] if 'signedURL' in response else str(response)
            else:
                raise Exception("Failed to generate signed URL")
                
        except Exception as e:
            logger.error(f"Failed to get signed URL: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get signed URL: {str(e)}")
    
    def update_folder_category(self, document_id: str, folder_category: str) -> Document:
        """
        Update the folder category of a document.
        """
        try:
            response = self.supabase.table("documents").update({
                "folder_category": folder_category,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", document_id).execute()
            
            if response.data:
                logger.info(f"Document folder updated: {document_id} -> {folder_category}")
                return Document(**response.data[0])
            else:
                raise HTTPException(status_code=404, detail="Document not found")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update document folder: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")