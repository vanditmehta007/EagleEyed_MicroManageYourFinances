from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import List, Optional
from backend.models.document_models import Document, DocumentUploadResponse
from backend.services.document_intake.document_service import DocumentIntakeService

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    client_id: str = Form(...),
    folder_category: Optional[str] = Form(None),
    service: DocumentIntakeService = Depends()
):
    """
    Upload a document (PDF/Image/Excel) for processing.
    """
    return await service.upload_document(file, client_id, folder_category)

@router.get("/", response_model=List[Document])
async def list_documents(
    client_id: str, 
    folder_category: Optional[str] = None,
    service: DocumentIntakeService = Depends()
):
    """
    List documents for a client, optionally filtered by folder.
    """
    return service.list_documents(client_id, folder_category)

@router.get("/{document_id}", response_model=Document)
async def get_document_metadata(
    document_id: str, 
    service: DocumentIntakeService = Depends()
):
    """
    Get metadata for a specific document.
    """
    return service.get_document(document_id)

@router.delete("/{document_id}")
async def delete_document(
    document_id: str, 
    service: DocumentIntakeService = Depends()
):
    """
    Soft delete a document.
    """
    return service.delete_document(document_id)

@router.post("/{document_id}/restore")
async def restore_document(
    document_id: str, 
    service: DocumentIntakeService = Depends()
):
    """
    Restore a soft-deleted document.
    """
    return service.restore_document(document_id)

@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    service: DocumentIntakeService = Depends()
):
    """
    Download a document file.
    """
    from fastapi.responses import StreamingResponse
    import io
    
    file_data = await service.download_document(document_id)
    document = service.get_document(document_id)
    
    return StreamingResponse(
        io.BytesIO(file_data),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={document.original_filename}"}
    )

@router.get("/{document_id}/preview")
async def preview_document(
    document_id: str,
    service: DocumentIntakeService = Depends()
):
    """
    Get a signed URL to preview the document.
    """
    url = service.get_signed_url(document_id)
    return {"url": url}
