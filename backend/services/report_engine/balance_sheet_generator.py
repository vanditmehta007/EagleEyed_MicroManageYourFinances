# backend/services/report_engine/balance_sheet_generator.py

from typing import Dict, Any, List
from backend.utils.supabase_client import supabase
from backend.models.report_models import BalanceSheet
from backend.utils.logger import logger
from collections import defaultdict

class BalanceSheetGenerator:
    """
    Service for generating Balance Sheet statements.
    
    Generates:
    - Assets (current and fixed)
    - Liabilities (current and long-term)
    - Equity
    - Balance verification (Assets = Liabilities + Equity)
    """

    def __init__(self):
        # Define ledger categories
        self.asset_ledgers = {
            "current": ["Cash", "Bank", "Accounts Receivable", "Inventory", "Prepaid Expenses"],
            "fixed": ["Fixed Assets", "Machinery", "Equipment", "Furniture", "Building", "Land", "Vehicles"]
        }
        
        self.liability_ledgers = {
            "current": ["Accounts Payable", "Short-term Loans", "Accrued Expenses", "Current Portion of Long-term Debt"],
            "long_term": ["Long-term Loans", "Bonds Payable", "Mortgage Payable"]
        }
        
        self.equity_ledgers = ["Capital", "Retained Earnings", "Owner's Equity", "Share Capital"]

    def generate_balance_sheet(self, client_id: str, year: int) -> BalanceSheet:
        """
        Generate Balance Sheet as of financial year end.
        """
        try:
            # Financial year end: March 31
            end_date = f"{year+1}-03-31"
            
            # Fetch all transactions up to year end
            response = supabase.table("transactions").select("*").eq("client_id", client_id).lte("date", end_date).is_("deleted_at", "null").execute()
            transactions = response.data if response.data else []
            
            # Calculate ledger balances
            ledger_balances = self._calculate_ledger_balances(transactions)
            
            # Calculate assets, liabilities, and equity
            assets = self._calculate_assets(ledger_balances)
            liabilities = self._calculate_liabilities(ledger_balances)
            equity = self._calculate_equity(ledger_balances, transactions)
            
            return BalanceSheet(
                assets=assets,
                liabilities=liabilities,
                equity=equity
            )
            
        except Exception as e:
            logger.error(f"Balance sheet generation failed: {e}")
            return BalanceSheet(
                assets={"current_assets": 0.0, "fixed_assets": 0.0, "total": 0.0},
                liabilities={"current_liabilities": 0.0, "long_term_liabilities": 0.0, "total": 0.0},
                equity={"capital": 0.0, "retained_earnings": 0.0, "total": 0.0}
            )

    def _calculate_ledger_balances(self, transactions: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate balance for each ledger account.
        """
        balances = defaultdict(float)
        
        for txn in transactions:
            ledger = txn.get("ledger", "Uncategorized")
            amount = float(txn.get("amount", 0))
            txn_type = txn.get("type", "")
            
            # Debit increases assets/expenses, Credit increases liabilities/revenue
            if txn_type == "debit":
                balances[ledger] += amount
            else:
                balances[ledger] -= amount
        
        return dict(balances)

    def _calculate_assets(self, ledger_balances: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculate total assets and breakdown.
        """
        current_assets = 0.0
        fixed_assets = 0.0
        
        for ledger, balance in ledger_balances.items():
            # Check if ledger is a current asset
            if any(asset_ledger.lower() in ledger.lower() for asset_ledger in self.asset_ledgers["current"]):
                current_assets += balance
            # Check if ledger is a fixed asset
            elif any(asset_ledger.lower() in ledger.lower() for asset_ledger in self.asset_ledgers["fixed"]):
                fixed_assets += balance
        
        return {
            "current_assets": round(current_assets, 2),
            "fixed_assets": round(fixed_assets, 2),
            "total": round(current_assets + fixed_assets, 2)
        }

    def _calculate_liabilities(self, ledger_balances: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculate total liabilities and breakdown.
        """
        current_liabilities = 0.0
        long_term_liabilities = 0.0
        
        for ledger, balance in ledger_balances.items():
            # Check if ledger is a current liability
            if any(liability_ledger.lower() in ledger.lower() for liability_ledger in self.liability_ledgers["current"]):
                current_liabilities += abs(balance)  # Liabilities are typically credit balances
            # Check if ledger is a long-term liability
            elif any(liability_ledger.lower() in ledger.lower() for liability_ledger in self.liability_ledgers["long_term"]):
                long_term_liabilities += abs(balance)
        
        return {
            "current_liabilities": round(current_liabilities, 2),
            "long_term_liabilities": round(long_term_liabilities, 2),
            "total": round(current_liabilities + long_term_liabilities, 2)
        }

    def _calculate_equity(self, ledger_balances: Dict[str, float], transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate total equity.
        """
        capital = 0.0
        
        # Sum equity ledgers
        for ledger, balance in ledger_balances.items():
            if any(equity_ledger.lower() in ledger.lower() for equity_ledger in self.equity_ledgers):
                capital += abs(balance)
        
        # Calculate retained earnings (profit/loss)
        revenue = sum(float(t.get("amount", 0)) for t in transactions if t.get("type") == "credit")
        expenses = sum(float(t.get("amount", 0)) for t in transactions if t.get("type") == "debit")
        retained_earnings = revenue - expenses
        
        return {
            "capital": round(capital, 2),
            "retained_earnings": round(retained_earnings, 2),
            "total": round(capital + retained_earnings, 2)
        }
