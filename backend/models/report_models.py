from typing import List
from pydantic import BaseModel

class ProfitAndLoss(BaseModel):
    revenue: float
    expenses: float
    gross_profit: float
    net_profit: float

class BalanceSheet(BaseModel):
    assets: dict
    liabilities: dict
    equity: dict

class TrialBalance(BaseModel):
    accounts: List[dict]
    total_debits: float = 0.0
    total_credits: float = 0.0
    is_balanced: bool = True
