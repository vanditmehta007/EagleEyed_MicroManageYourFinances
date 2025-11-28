
from typing import List, Dict, Any, Optional
from backend.services.compliance_engine.gst_compliance import GSTComplianceService
from backend.services.compliance_engine.tds_engine import TDSEngine
from backend.utils.logger import logger

# Initialize services
_gst_service = GSTComplianceService()
_tds_engine = TDSEngine()

def gst_check(transaction_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Run GST compliance checks (ITC eligibility, RCM) on a list of transactions.
    """
    results = _gst_service.check_compliance(transaction_ids)
    # Convert Pydantic models to dicts for token efficiency
    return [result.model_dump() if hasattr(result, 'model_dump') else result.__dict__ for result in results]

def gst_reconcile(client_id: str, month: int, year: int) -> Dict[str, Any]:
    """
    Reconcile purchase register with GSTR-2B for a specific month.
    """
    return _gst_service.reconcile_gstr2b(client_id, month, year)

def tds_check(transaction_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Check TDS applicability and section for a list of transactions.
    """
    results = _tds_engine.check_tds(transaction_ids)
    # Convert Pydantic models to dicts for token efficiency
    return [result.model_dump() if hasattr(result, 'model_dump') else result.__dict__ for result in results]

def tds_calculate(amount: float, section: str) -> Dict[str, Any]:
    """
    Calculate TDS amount based on section and transaction amount.
    """
    tds_amount = _tds_engine.calculate_tds_amount(amount, section)
    return {
        "section": section,
        "transaction_amount": amount,
        "tds_amount": tds_amount,
        "net_payable": amount - tds_amount
    }

# Tool Registry Export
COMPLIANCE_TOOLS = {
    "gst_check": gst_check,
    "gst_reconcile": gst_reconcile,
    "tds_check": tds_check,
    "tds_calculate": tds_calculate
}
