# backend/routers/ocr_router.py

from fastapi import APIRouter, UploadFile, File, Depends
from backend.services.ocr.ocr_service import OCRService
from backend.models.response_models import SuccessResponse

router = APIRouter(prefix="/ocr", tags=["OCR"])

def get_ocr_service() -> OCRService:
    """Dependency to get OCRService instance."""
    return OCRService()

@router.post("/extract-text", response_model=SuccessResponse)
async def extract_text(
    file: UploadFile = File(...),
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """
    Extract text from an image or PDF using OCR.
    """
    return ocr_service.extract_text(file)

@router.post("/extract-table", response_model=SuccessResponse)
async def extract_table(
    file: UploadFile = File(...),
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """
    Extract tabular data from a document.
    """
    return ocr_service.extract_table(file)
