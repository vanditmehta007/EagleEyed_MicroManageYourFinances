from typing import List
from pydantic import BaseModel

class GSTR1Summary(BaseModel):
    total_taxable: float
    b2b: float
    b2c: float
    exports: float
    nil_rated: float

class GSTR3BSummary(BaseModel):
    outward_tax: float
    eligible_itc: float
    rcm_tax: float
    net_payable: float

class TDSSummary(BaseModel):
    total_tds: float
    vendor_breakdown: List[dict]
