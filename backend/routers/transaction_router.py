from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Optional
from backend.models.transaction_models import Transaction, TransactionCreate
from backend.services.transaction_service import TransactionService
from backend.services.transaction_extraction_service import TransactionExtractionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/", response_model=Transaction)
async def create_transaction(
    transaction: TransactionCreate, 
    sheet_id: str,
    client_id: str,
    service: TransactionService = Depends()
):
    """
    Manually create a single transaction.
    """
    return service.create_transaction(transaction, sheet_id, client_id)

@router.get("/{transaction_id}", response_model=Transaction)
async def get_transaction(
    transaction_id: str, 
    service: TransactionService = Depends()
):
    """
    Get details of a specific transaction.
    """
    return service.get_transaction(transaction_id)

@router.put("/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: str, 
    updates: dict, 
    service: TransactionService = Depends()
):
    """
    Update transaction details (e.g., description, amount, ledger).
    """
    return service.update_transaction(transaction_id, updates)

@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: str, 
    service: TransactionService = Depends()
):
    """
    Soft delete a transaction.
    """
    return service.delete_transaction(transaction_id)

@router.post("/{transaction_id}/restore")
async def restore_transaction(
    transaction_id: str, 
    service: TransactionService = Depends()
):
    """
    Restore a soft-deleted transaction.
    """
    return service.restore_transaction(transaction_id)

@router.get("/", response_model=List[Transaction])
async def list_transactions(
    client_id: str,
    sheet_id: Optional[str] = None,
    ledger: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    service: TransactionService = Depends()
):
    """
    List transactions with optional filters.
    """
    return service.list_transactions(client_id, sheet_id, ledger, start_date, end_date)

# New endpoints for bank statement extraction
@router.get("/extract/client/{client_id}")
async def get_client_bank_transactions(
    client_id: str,
    request: Request,
    service: TransactionExtractionService = Depends()
):
    """
    Get all transactions for a client from bank statements, organized by year and month.
    Extracts transactions from bank statement documents using OCR.
    """
    try:
        transactions = service.get_transactions_by_client(client_id)
        return transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get transactions: {str(e)}")

@router.get("/extract/document/{document_id}")
async def get_document_bank_transactions(
    document_id: str,
    request: Request,
    service: TransactionExtractionService = Depends()
):
    """
    Get transactions from a specific bank statement document using OCR.
    """
    try:
        transactions = service.extract_transactions_from_document(document_id)
        return {"transactions": transactions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract transactions: {str(e)}")
