from typing import Optional
from pydantic import BaseModel

class GSTComplianceResult(BaseModel):
    transaction_id: str
    itc_eligible: bool
    rcm_applicable: bool
    mismatch_reason: Optional[str]
    law_reference: Optional[str]

class TDSCheckResult(BaseModel):
    transaction_id: str
    tds_applicable: bool
    section: Optional[str]
    threshold: Optional[float]
    reason: Optional[str]

class DisallowanceResult(BaseModel):
    transaction_id: str
    section: str
    reason: str
