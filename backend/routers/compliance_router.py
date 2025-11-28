from fastapi import APIRouter, Depends
from typing import List
from backend.models.compliance_models import GSTComplianceResult, TDSCheckResult, DisallowanceResult
from backend.services.compliance_engine.gst_compliance import GSTComplianceService
from backend.services.compliance_engine.tds_engine import TDSEngine
from backend.services.compliance_engine.disallowance_checker import DisallowanceChecker
from backend.services.compliance_engine.depreciation_engine import DepreciationEngine
from backend.services.compliance_engine.msme_compliance import MSMEComplianceService

router = APIRouter(prefix="/compliance", tags=["Compliance"])

@router.post("/check-gst", response_model=List[GSTComplianceResult])
async def check_gst_compliance(
    transaction_ids: List[str], 
    service: GSTComplianceService = Depends()
):
    """
    Run GST compliance checks (ITC eligibility, RCM, mismatches).
    """
    return service.check_compliance(transaction_ids)

@router.post("/check-tds", response_model=List[TDSCheckResult])
async def check_tds_applicability(
    transaction_ids: List[str], 
    service: TDSEngine = Depends()
):
    """
    Run TDS applicability checks based on thresholds and sections.
    """
    return service.check_tds(transaction_ids)

@router.post("/check-disallowances", response_model=List[DisallowanceResult])
async def check_disallowances(
    transaction_ids: List[str], 
    service: DisallowanceChecker = Depends()
):
    """
    Check for expenses disallowed under Income Tax Act (e.g., 40(a)(ia), 40A(3)).
    """
    return service.check_disallowances(transaction_ids)

@router.post("/calculate-depreciation")
async def calculate_depreciation(
    asset_ids: List[str], 
    service: DepreciationEngine = Depends()
):
    """
    Calculate depreciation as per Income Tax Act block of assets.
    """
    return service.calculate_depreciation(asset_ids)

@router.post("/check-msme")
async def check_msme_compliance(
    vendor_ids: List[str], 
    service: MSMEComplianceService = Depends()
):
    """
    Check for MSME payment delays and interest obligations.
    """
    return service.check_msme_status(vendor_ids)
