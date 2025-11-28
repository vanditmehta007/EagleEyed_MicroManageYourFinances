
from typing import Dict, Any
from backend.services.report_engine.pnl_generator import PnLGenerator
from backend.services.report_engine.balance_sheet_generator import BalanceSheetGenerator
from backend.services.report_engine.trial_balance_generator import TrialBalanceGenerator
from backend.services.report_engine.cashflow_generator import CashflowGenerator

# Initialize services
_pnl_generator = PnLGenerator()
_balance_sheet_generator = BalanceSheetGenerator()
_trial_balance_generator = TrialBalanceGenerator()
_cashflow_generator = CashflowGenerator()

def generate_pnl(client_id: str, year: int) -> Dict[str, Any]:
    """
    Generate Profit & Loss statement for a financial year.
    """
    result = _pnl_generator.generate_pnl(client_id, year)
    # Convert Pydantic model to dict
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__

def generate_balance_sheet(client_id: str, year: int) -> Dict[str, Any]:
    """
    Generate Balance Sheet as of financial year end.
    """
    result = _balance_sheet_generator.generate_balance_sheet(client_id, year)
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__

def generate_trial_balance(client_id: str, year: int) -> Dict[str, Any]:
    """
    Generate Trial Balance for a financial year.
    """
    result = _trial_balance_generator.generate_trial_balance(client_id, year)
    return result.model_dump() if hasattr(result, 'model_dump') else result.__dict__

def generate_cashflow(client_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Generate Cash Flow statement for a specific date range.
    """
    return _cashflow_generator.generate(client_id, start_date, end_date)

# Tool Registry Export
REPORT_TOOLS = {
    "generate_pnl": generate_pnl,
    "generate_balance_sheet": generate_balance_sheet,
    "generate_trial_balance": generate_trial_balance,
    "generate_cashflow": generate_cashflow
}
