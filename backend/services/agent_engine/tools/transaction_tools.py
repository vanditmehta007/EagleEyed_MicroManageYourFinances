
from typing import List, Optional, Dict, Any
from backend.services.transaction_service import TransactionService
from backend.services.ledger_classifier.ledger_classifier_service import LedgerClassifierService
from backend.services.red_flag_engine.anomaly_detector import AnomalyDetectorService
from backend.models.transaction_models import TransactionCreate, TransactionUpdate
from backend.utils.logger import logger

# Initialize services
_transaction_service = TransactionService()
_ledger_classifier = LedgerClassifierService()
_anomaly_detector = AnomalyDetectorService()

def get_transactions(
    sheet_id: Optional[str] = None,
    ledger: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    List transactions with optional filters.
    """
    return _transaction_service.list_transactions(
        sheet_id=sheet_id,
        ledger=ledger,
        date_from=date_from,
        date_to=date_to,
        limit=limit
    )

def create_transaction(
    amount: float,
    date: str,
    description: str,
    type: str,
    client_id: str,
    ledger: Optional[str] = None,
    gstin: Optional[str] = None,
    invoice_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new financial transaction.
    """
    txn_data = TransactionCreate(
        amount=amount,
        date=date,
        description=description,
        type=type,
        client_id=client_id,
        ledger=ledger,
        gstin=gstin,
        invoice_number=invoice_number
    )
    return _transaction_service.create_transaction(txn_data)

def update_transaction(
    transaction_id: str,
    amount: Optional[float] = None,
    ledger: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing transaction.
    """
    update_data = TransactionUpdate(
        amount=amount,
        ledger=ledger,
        description=description
    )
    return _transaction_service.update_transaction(transaction_id, update_data)

def delete_transaction(transaction_id: str) -> Dict[str, str]:
    """
    Soft delete a transaction.
    """
    _transaction_service.delete_transaction(transaction_id)
    return {"status": "success", "message": f"Transaction {transaction_id} deleted"}

def classify_transaction(transaction_id: str) -> Dict[str, Any]:
    """
    Trigger AI ledger classification for a single transaction.
    """
    # The service takes a list, so we wrap the single ID
    results = _ledger_classifier.classify_transactions([transaction_id])
    return results[0] if results else {"error": "Classification failed"}

def detect_anomalies(client_id: str) -> Dict[str, Any]:
    """
    Run a full anomaly scan for a client and return red flags.
    """
    # Run scan first
    _anomaly_detector.run_scan(client_id)
    # Then fetch results
    flags = _anomaly_detector.get_red_flags(client_id)
    return {"client_id": client_id, "red_flags": flags}

# Tool Registry Export
TRANSACTION_TOOLS = {
    "get_transactions": get_transactions,
    "create_transaction": create_transaction,
    "update_transaction": update_transaction,
    "delete_transaction": delete_transaction,
    "classify_transaction": classify_transaction,
    "detect_anomalies": detect_anomalies
}
