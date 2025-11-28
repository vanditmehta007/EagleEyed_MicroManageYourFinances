from fastapi import APIRouter, Depends
from backend.models.report_models import ProfitAndLoss, BalanceSheet, TrialBalance
from backend.services.report_engine.pnl_generator import PnLGenerator
from backend.services.report_engine.balance_sheet_generator import BalanceSheetGenerator
from backend.services.report_engine.trial_balance_generator import TrialBalanceGenerator
from backend.services.report_engine.cashflow_report import CashflowGenerator
from backend.services.report_engine.working_paper_generator import WorkingPaperGenerator

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/pnl", response_model=ProfitAndLoss)
async def get_pnl(
    client_id: str, 
    year: int, 
    service: PnLGenerator = Depends()
):
    """
    Generate Profit & Loss statement.
    """
    return service.generate_pnl(client_id, year)

@router.get("/balance-sheet", response_model=BalanceSheet)
async def get_balance_sheet(
    client_id: str, 
    year: int, 
    service: BalanceSheetGenerator = Depends()
):
    """
    Generate Balance Sheet.
    """
    return service.generate_balance_sheet(client_id, year)

@router.get("/trial-balance", response_model=TrialBalance)
async def get_trial_balance(
    client_id: str, 
    year: int, 
    service: TrialBalanceGenerator = Depends()
):
    """
    Generate Trial Balance.
    """
    return service.generate_trial_balance(client_id, year)

@router.get("/cashflow")
async def get_cashflow(
    client_id: str, 
    year: int, 
    service: CashflowGenerator = Depends()
):
    """
    Generate Cashflow Statement.
    """
    return service.generate_cashflow(client_id, year)

@router.get("/working-papers")
async def get_working_papers(
    client_id: str, 
    year: int, 
    service: WorkingPaperGenerator = Depends()
):
    """
    Generate Year-End Working Papers.
    """
    return service.generate(client_id, year)
