# backend/services/report_engine/working_paper_generator.py

from typing import Dict, Any, List
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger
from collections import defaultdict

class WorkingPaperGenerator:
    """
    Service for generating audit working papers.
    
    Generates:
    - Ledger reconciliations
    - Adjustment entries
    - Supporting schedules
    - Audit trail documentation
    """

    def __init__(self) -> None:
        # Define ledgers that require reconciliation
        self.reconciliation_ledgers = [
            "Bank", "Cash", "Accounts Receivable", "Accounts Payable",
            "Inventory", "Fixed Assets", "Loans"
        ]
        
        # Define common adjustment types
        self.adjustment_types = [
            "Depreciation",
            "Accrued Expenses",
            "Prepaid Expenses",
            "Accrued Income",
            "Deferred Income",
            "Provision for Bad Debts"
        ]

    def generate(self, client_id: str, financial_year: int) -> Dict[str, Any]:
        """
        Generate working papers for a financial year.
        """
        try:
            logger.info(f"Generating working papers for client {client_id} (FY {financial_year})")
            
            # Fetch all relevant data for the financial year
            start_date = f"{financial_year}-04-01"
            end_date = f"{financial_year+1}-03-31"
            
            response = supabase.table("transactions").select("*").eq("client_id", client_id).gte("date", start_date).lte("date", end_date).is_("deleted_at", "null").execute()
            
            transactions = response.data if response.data else []
            
            # Generate working paper sections
            working_papers = {
                "client_id": client_id,
                "financial_year": f"{financial_year}-{financial_year+1}",
                "reconciliations": self._generate_reconciliations(client_id, financial_year, transactions),
                "adjustments": self._generate_adjustments(client_id, financial_year, transactions),
                "supporting_schedules": self._generate_supporting_schedules(client_id, financial_year, transactions),
                "audit_trail": self._generate_audit_trail(client_id, financial_year, transactions)
            }
            
            return working_papers
            
        except Exception as e:
            logger.error(f"Working paper generation failed: {e}")
            return {
                "client_id": client_id,
                "financial_year": f"{financial_year}-{financial_year+1}",
                "error": str(e)
            }

    def _generate_reconciliations(self, client_id: str, year: int, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate ledger reconciliation schedules.
        """
        reconciliations = []
        
        # Group transactions by ledger
        ledger_groups = defaultdict(list)
        for txn in transactions:
            ledger = txn.get("ledger", "Uncategorized")
            ledger_groups[ledger].append(txn)
        
        # Generate reconciliation for each important ledger
        for ledger_name in self.reconciliation_ledgers:
            # Find matching ledger (case-insensitive partial match)
            matching_ledgers = [
                ledger for ledger in ledger_groups.keys()
                if ledger_name.lower() in ledger.lower()
            ]
            
            for ledger in matching_ledgers:
                txns = ledger_groups[ledger]
                
                # Calculate opening and closing balances
                opening_balance = 0.0
                closing_balance = 0.0
                total_debits = 0.0
                total_credits = 0.0
                
                for txn in txns:
                    amount = float(txn.get("amount", 0))
                    if txn.get("type") == "debit":
                        total_debits += amount
                        closing_balance += amount
                    else:
                        total_credits += amount
                        closing_balance -= amount
                
                reconciliations.append({
                    "ledger_name": ledger,
                    "opening_balance": round(opening_balance, 2),
                    "total_debits": round(total_debits, 2),
                    "total_credits": round(total_credits, 2),
                    "closing_balance": round(closing_balance, 2),
                    "transaction_count": len(txns),
                    "reconciliation_status": "To be verified",
                    "notes": f"Reconciliation for {ledger} - verify with supporting documents"
                })
        
        return reconciliations

    def _generate_adjustments(self, client_id: str, year: int, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate adjustment entry schedules.
        """
        adjustments = []
        
        # Calculate depreciation adjustment
        fixed_asset_value = 0.0
        for txn in transactions:
            ledger = str(txn.get("ledger", "")).lower()
            if "fixed asset" in ledger or "machinery" in ledger or "equipment" in ledger:
                if txn.get("type") == "debit":
                    fixed_asset_value += float(txn.get("amount", 0))
        
        if fixed_asset_value > 0:
            depreciation_amount = fixed_asset_value * 0.15  # 15% depreciation
            adjustments.append({
                "adjustment_type": "Depreciation",
                "description": "Depreciation on Fixed Assets @ 15%",
                "debit_account": "Depreciation Expense",
                "credit_account": "Accumulated Depreciation",
                "amount": round(depreciation_amount, 2),
                "narration": f"Depreciation for FY {year}-{year+1}"
            })
        
        # Accrued expenses adjustment (placeholder)
        adjustments.append({
            "adjustment_type": "Accrued Expenses",
            "description": "Accrued but unpaid expenses",
            "debit_account": "Expense Account",
            "credit_account": "Accrued Expenses Payable",
            "amount": 0.0,
            "narration": "To be calculated based on invoices received post year-end"
        })
        
        # Prepaid expenses adjustment (placeholder)
        adjustments.append({
            "adjustment_type": "Prepaid Expenses",
            "description": "Expenses paid in advance",
            "debit_account": "Prepaid Expenses",
            "credit_account": "Expense Account",
            "amount": 0.0,
            "narration": "To be calculated based on insurance, rent, etc."
        })
        
        return adjustments

    def _generate_supporting_schedules(self, client_id: str, year: int, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate supporting schedules for audit.
        """
        # Revenue schedule
        revenue_txns = [t for t in transactions if t.get("type") == "credit"]
        total_revenue = sum(float(t.get("amount", 0)) for t in revenue_txns)
        
        # Expense schedule
        expense_txns = [t for t in transactions if t.get("type") == "debit"]
        total_expenses = sum(float(t.get("amount", 0)) for t in expense_txns)
        
        # Group expenses by category
        expense_by_category = defaultdict(float)
        for txn in expense_txns:
            ledger = txn.get("ledger", "Uncategorized")
            amount = float(txn.get("amount", 0))
            expense_by_category[ledger] += amount
        
        return {
            "revenue_schedule": {
                "total_revenue": round(total_revenue, 2),
                "transaction_count": len(revenue_txns),
                "largest_transaction": round(max([float(t.get("amount", 0)) for t in revenue_txns], default=0), 2)
            },
            "expense_schedule": {
                "total_expenses": round(total_expenses, 2),
                "transaction_count": len(expense_txns),
                "by_category": {k: round(v, 2) for k, v in expense_by_category.items()}
            },
            "net_profit": round(total_revenue - total_expenses, 2)
        }

    def _generate_audit_trail(self, client_id: str, year: int, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate audit trail documentation.
        """
        # Analyze transaction patterns
        total_transactions = len(transactions)
        
        # Identify high-value transactions (> 1,00,000)
        high_value_txns = [t for t in transactions if float(t.get("amount", 0)) > 100000]
        
        # Identify transactions without supporting documents
        missing_docs = [t for t in transactions if not t.get("invoice_number")]
        
        return {
            "total_transactions": total_transactions,
            "high_value_transactions": {
                "count": len(high_value_txns),
                "total_amount": round(sum(float(t.get("amount", 0)) for t in high_value_txns), 2),
                "note": "Verify supporting documents for all high-value transactions"
            },
            "missing_documentation": {
                "count": len(missing_docs),
                "note": "Obtain invoices/receipts for transactions without documentation"
            },
            "audit_recommendations": [
                "Verify bank reconciliation statements",
                "Confirm receivables and payables with parties",
                "Physical verification of inventory and fixed assets",
                "Review related party transactions",
                "Check compliance with tax regulations"
            ]
        }
