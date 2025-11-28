# backend/services/report_engine/cashflow_generator.py

from typing import Dict, Any, List
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger

class CashflowGenerator:
    """
    Service for generating Cash Flow statements.
    
    Generates:
    - Operating activities cash flow
    - Investing activities cash flow
    - Financing activities cash flow
    - Net cash flow
    """

    def __init__(self) -> None:
        # Define activity categories
        self.operating_ledgers = [
            "Sales", "Revenue", "Purchase", "Salary", "Rent", "Utilities",
            "Professional Fees", "Office Supplies", "Travel", "Insurance"
        ]
        
        self.investing_ledgers = [
            "Fixed Assets", "Machinery", "Equipment", "Furniture", "Building",
            "Land", "Vehicles", "Investment"
        ]
        
        self.financing_ledgers = [
            "Loan", "Capital", "Owner's Equity", "Share Capital", "Dividend",
            "Bonds", "Mortgage"
        ]

    def generate(self, client_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Generate Cash Flow statement for a date range.
        """
        try:
            # Fetch all transactions in date range
            response = supabase.table("transactions").select("*").eq("client_id", client_id).gte("date", start_date).lte("date", end_date).is_("deleted_at", "null").execute()
            
            transactions = response.data if response.data else []
            
            # Calculate cash flows for each category
            operating_cf = self._calculate_operating_cashflow(transactions)
            investing_cf = self._calculate_investing_cashflow(transactions)
            financing_cf = self._calculate_financing_cashflow(transactions)
            
            # Calculate net cash flow
            net_cashflow = operating_cf + investing_cf + financing_cf
            
            return {
                "operating_activities": round(operating_cf, 2),
                "investing_activities": round(investing_cf, 2),
                "financing_activities": round(financing_cf, 2),
                "net_cashflow": round(net_cashflow, 2),
                "period": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
            
        except Exception as e:
            logger.error(f"Cash flow generation failed: {e}")
            return {
                "operating_activities": 0.0,
                "investing_activities": 0.0,
                "financing_activities": 0.0,
                "net_cashflow": 0.0,
                "error": str(e)
            }

    def _calculate_operating_cashflow(self, transactions: List[Dict[str, Any]]) -> float:
        """
        Calculate cash flow from operating activities.
        
        Operating activities include:
        - Cash receipts from sales
        - Cash payments to suppliers
        - Cash payments for salaries, rent, utilities
        """
        operating_cf = 0.0
        
        for txn in transactions:
            ledger = txn.get("ledger", "")
            amount = float(txn.get("amount", 0))
            txn_type = txn.get("type", "")
            
            # Check if transaction is operating activity
            is_operating = any(op_ledger.lower() in ledger.lower() for op_ledger in self.operating_ledgers)
            
            if is_operating:
                # Credit (revenue) increases cash, Debit (expense) decreases cash
                if txn_type == "credit":
                    operating_cf += amount
                else:
                    operating_cf -= amount
        
        return operating_cf

    def _calculate_investing_cashflow(self, transactions: List[Dict[str, Any]]) -> float:
        """
        Calculate cash flow from investing activities.
        
        Investing activities include:
        - Purchase of fixed assets (cash outflow)
        - Sale of fixed assets (cash inflow)
        - Purchase/sale of investments
        """
        investing_cf = 0.0
        
        for txn in transactions:
            ledger = txn.get("ledger", "")
            amount = float(txn.get("amount", 0))
            txn_type = txn.get("type", "")
            
            # Check if transaction is investing activity
            is_investing = any(inv_ledger.lower() in ledger.lower() for inv_ledger in self.investing_ledgers)
            
            if is_investing:
                # Purchase of assets (debit) is cash outflow
                # Sale of assets (credit) is cash inflow
                if txn_type == "credit":
                    investing_cf += amount
                else:
                    investing_cf -= amount
        
        return investing_cf

    def _calculate_financing_cashflow(self, transactions: List[Dict[str, Any]]) -> float:
        """
        Calculate cash flow from financing activities.
        
        Financing activities include:
        - Proceeds from loans (cash inflow)
        - Repayment of loans (cash outflow)
        - Capital contributions (cash inflow)
        - Dividend payments (cash outflow)
        """
        financing_cf = 0.0
        
        for txn in transactions:
            ledger = txn.get("ledger", "")
            amount = float(txn.get("amount", 0))
            txn_type = txn.get("type", "")
            
            # Check if transaction is financing activity
            is_financing = any(fin_ledger.lower() in ledger.lower() for fin_ledger in self.financing_ledgers)
            
            if is_financing:
                # Loan proceeds/capital (credit) is cash inflow
                # Loan repayment/dividend (debit) is cash outflow
                if txn_type == "credit":
                    financing_cf += amount
                else:
                    financing_cf -= amount
        
        return financing_cf
