from fastapi import APIRouter, Depends
from typing import List
from backend.models.sheet_models import Sheet, SheetCreate
from backend.models.transaction_models import Transaction
from backend.services.sheet_service import SheetService

router = APIRouter(prefix="/sheets", tags=["Sheets"])

@router.post("/", response_model=Sheet)
async def create_sheet(
    sheet: SheetCreate, 
    client_id: str,
    service: SheetService = Depends()
):
    """
    Create a new monthly sheet for a client.
    """
    return service.create_sheet(client_id, sheet)

@router.get("/", response_model=List[Sheet])
async def list_sheets(
    client_id: str, 
    service: SheetService = Depends()
):
    """
    List all sheets for a client.
    """
    return service.list_sheets(client_id)

@router.get("/{sheet_id}", response_model=Sheet)
async def get_sheet(
    sheet_id: str, 
    service: SheetService = Depends()
):
    """
    Get sheet metadata.
    """
    return service.get_sheet(sheet_id)

@router.get("/{sheet_id}/transactions", response_model=List[Transaction])
async def get_sheet_transactions(
    sheet_id: str, 
    service: SheetService = Depends()
):
    """
    Get all transactions within a sheet.
    """
    return service.get_transactions(sheet_id)

@router.delete("/{sheet_id}")
async def delete_sheet(
    sheet_id: str, 
    service: SheetService = Depends()
):
    """
    Soft delete a sheet.
    """
    return service.delete_sheet(sheet_id)

@router.post("/{sheet_id}/restore")
async def restore_sheet(
    sheet_id: str, 
    service: SheetService = Depends()
):
    """
    Restore a soft-deleted sheet.
    """
    return service.restore_sheet(sheet_id)
