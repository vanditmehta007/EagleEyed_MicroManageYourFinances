from fastapi import APIRouter, Depends
from typing import List
from backend.models.ledger_models import LedgerClassification
from backend.services.ledger_classifier.ledger_classifier_service import LedgerClassifierService

router = APIRouter(prefix="/ledger", tags=["Ledger Classification"])

@router.post("/classify", response_model=List[LedgerClassification])
async def classify_transactions(
    transaction_ids: List[str], 
    service: LedgerClassifierService = Depends()
):
    """
    Trigger AI-based ledger classification for a list of transactions.
    """
    return service.classify_transactions(transaction_ids)

@router.post("/override", response_model=LedgerClassification)
async def override_classification(
    transaction_id: str, 
    new_ledger: str, 
    reason: str,
    service: LedgerClassifierService = Depends()
):
    """
    CA override for a specific transaction's ledger classification.
    """
    return service.override_classification(transaction_id, new_ledger, reason)

@router.get("/logs/{transaction_id}", response_model=List[LedgerClassification])
async def get_classification_history(
    transaction_id: str, 
    service: LedgerClassifierService = Depends()
):
    """
    Get the history of classifications and overrides for a transaction.
    """
    return service.get_classification_history(transaction_id)
