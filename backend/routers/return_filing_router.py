from fastapi import APIRouter, Depends
from backend.models.return_filing_models import GSTR1Summary, GSTR3BSummary, TDSSummary
from backend.services.return_filing.gstr1_prepare import GSTR1Service
from backend.services.return_filing.gstr3b_prepare import GSTR3BService
from backend.services.return_filing.tds_summary import TDSSummaryService
from backend.services.return_filing.advance_tax_calc import AdvanceTaxService
from backend.services.return_filing.reconciliation_service import ReconciliationService

router = APIRouter(prefix="/returns", tags=["Return Filing"])

@router.get("/gstr1", response_model=GSTR1Summary)
async def prepare_gstr1(
    client_id: str, 
    month: int, 
    year: int, 
    service: GSTR1Service = Depends()
):
    """
    Prepare GSTR-1 summary (Outward Supplies).
    """
    return service.prepare_gstr1(client_id, month, year)

@router.get("/gstr3b", response_model=GSTR3BSummary)
async def prepare_gstr3b(
    client_id: str, 
    month: int, 
    year: int, 
    service: GSTR3BService = Depends()
):
    """
    Prepare GSTR-3B summary (ITC, Tax Liability).
    """
    return service.prepare_gstr3b(client_id, month, year)

@router.get("/tds-summary", response_model=TDSSummary)
async def get_tds_summary(
    client_id: str, 
    quarter: int, 
    year: int, 
    service: TDSSummaryService = Depends()
):
    """
    Generate TDS return summary.
    """
    return service.generate_summary(client_id, quarter, year)

@router.get("/advance-tax")
async def calculate_advance_tax(
    client_id: str, 
    quarter: int, 
    year: int, 
    service: AdvanceTaxService = Depends()
):
    """
    Calculate Advance Tax liability.
    """
    return service.calculate_tax(client_id, quarter, year)

@router.post("/reconcile")
async def run_reconciliation(
    client_id: str, 
    month: int, 
    year: int, 
    service: ReconciliationService = Depends()
):
    """
    Run reconciliation (e.g., GSTR-2B vs Books).
    """
    return service.reconcile(client_id, month, year)
