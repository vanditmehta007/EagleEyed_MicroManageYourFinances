from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import List
from backend.models.response_models import SuccessResponse
from backend.services.sheet_service import SheetService

router = APIRouter(prefix="/import", tags=["Import"])

@router.post("/excel-csv")
async def import_excel_csv(
    file: UploadFile = File(...),
    client_id: str = Form(...),
    sheet_id: str = Form(...),
    service: SheetService = Depends()
):
    """
    Import transactions from Excel or CSV files.
    """
    return service.import_transactions(file, client_id, sheet_id)

@router.post("/json")
async def import_json(
    file: UploadFile = File(...),
    client_id: str = Form(...),
    sheet_id: str = Form(...),
    service: SheetService = Depends()
):
    """
    Import transactions from JSON files.
    """
    return service.import_json(file, client_id, sheet_id)

@router.post("/zoho-books")
async def import_zoho_books(
    client_id: str,
    api_key: str,
    organization_id: str,
    service: SheetService = Depends()
):
    """
    Import data from Zoho Books integration.
    """
    return service.import_from_zoho(client_id, api_key, organization_id)

@router.post("/khatabook")
async def import_khatabook(
    file: UploadFile = File(...),
    client_id: str = Form(...),
    service: SheetService = Depends()
):
    """
    Import data from Khatabook export.
    """
    return service.import_from_khatabook(file, client_id)
