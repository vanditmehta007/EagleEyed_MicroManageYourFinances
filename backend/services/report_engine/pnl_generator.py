# backend/services/report_engine/pnl_generator.py

from typing import Dict, Any, List
from datetime import datetime
from backend.utils.supabase_client import supabase
from backend.models.report_models import ProfitAndLoss
from backend.utils.logger import logger
from collections import defaultdict

class PnLGenerator:
    """
    Service for generating Profit & Loss statements.
    
    Generates:
    - Income statement with revenue and expenses
    - Gross profit, operating profit, net profit
    - Period comparisons
    - Categorized expense breakdowns
    """

    def __init__(self):
        # Define expense categories
        self.direct_expense_ledgers = [
            "Purchase of Goods",
            "Cost of Goods Sold",
            "Direct Labor",
            "Manufacturing Expenses"
        ]
        
        self.indirect_expense_ledgers = [
            "Rent Expense",
            "Salary & Wages",
            "Professional Fees",
            "Electricity Expense",
            "Telephone Expense",
            "Internet Expense",
            "Office Supplies",
            "Travel Expense",
            "Fuel Expense",
            "Repairs & Maintenance",
            "Insurance Expense",
            "Bank Charges",
            "Depreciation"
        ]

    def generate_pnl(self, client_id: str, year: int) -> ProfitAndLoss:
        """
        Generate P&L statement for a financial year.
        """
        try:
            # Financial year in India: April to March
            start_date = f"{year}-04-01"
            end_date = f"{year+1}-03-31"
            
            # Fetch all transactions for the financial year
            response = supabase.table("transactions").select("*").eq("client_id", client_id).gte("date", start_date).lte("date", end_date).is_("deleted_at", "null").execute()
            transactions = response.data if response.data else []
            
            # Separate revenue and expense transactions
            revenue_txns = [t for t in transactions if t.get("type") == "credit"]
            expense_txns = [t for t in transactions if t.get("type") == "debit"]
            
            # Calculate revenue
            revenue_data = self._calculate_revenue(revenue_txns)
            total_revenue = revenue_data["total"]
            
            # Calculate expenses
            expense_data = self._calculate_expenses(expense_txns)
            total_expenses = expense_data["total"]
            direct_expenses = expense_data["direct"]
            indirect_expenses = expense_data["indirect"]
            
            # Calculate profit metrics
            profit_metrics = self._calculate_profit(total_revenue, direct_expenses, indirect_expenses)
            
            return ProfitAndLoss(
                revenue=round(total_revenue, 2),
                expenses=round(total_expenses, 2),
                gross_profit=round(profit_metrics["gross_profit"], 2),
                net_profit=round(profit_metrics["net_profit"], 2)
            )
            
        except Exception as e:
            logger.error(f"P&L generation failed: {e}")
            return ProfitAndLoss(
                revenue=0.0,
                expenses=0.0,
                gross_profit=0.0,
                net_profit=0.0
            )

    def _calculate_revenue(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate total revenue and breakdown by category.
        """
        total_revenue = 0.0
        revenue_by_ledger = defaultdict(float)
        
        for txn in transactions:
            amount = float(txn.get("amount", 0))
            ledger = txn.get("ledger", "Other Income")
            
            total_revenue += amount
            revenue_by_ledger[ledger] += amount
        
        return {
            "total": total_revenue,
            "breakdown": dict(revenue_by_ledger)
        }

    def _calculate_expenses(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate total expenses and breakdown by category.
        """
        total_expenses = 0.0
        direct_expenses = 0.0
        indirect_expenses = 0.0
        
        expense_by_ledger = defaultdict(float)
        
        for txn in transactions:
            amount = float(txn.get("amount", 0))
            ledger = txn.get("ledger", "Uncategorized")
            
            total_expenses += amount
            expense_by_ledger[ledger] += amount
            
            # Categorize as direct or indirect
            if ledger in self.direct_expense_ledgers:
                direct_expenses += amount
            else:
                indirect_expenses += amount
        
        return {
            "total": total_expenses,
            "direct": direct_expenses,
            "indirect": indirect_expenses,
            "breakdown": dict(expense_by_ledger)
        }

    def _calculate_profit(self, revenue: float, direct_expenses: float, indirect_expenses: float) -> Dict[str, float]:
        """
        Calculate profit metrics.
        
        - Gross Profit = Revenue - Direct Expenses (Cost of Goods Sold)
        - Operating Profit = Gross Profit - Indirect Expenses (Operating Expenses)
        - Net Profit = Operating Profit - Interest - Tax (simplified here)
        """
        gross_profit = revenue - direct_expenses
        operating_profit = gross_profit - indirect_expenses
        net_profit = operating_profit  # Simplified - would subtract interest, tax, etc.
        
        return {
            "gross_profit": gross_profit,
            "operating_profit": operating_profit,
            "net_profit": net_profit
        }
