# backend/services/report_engine/trial_balance_generator.py

from typing import Dict, Any, List
from backend.utils.supabase_client import supabase
from backend.models.report_models import TrialBalance
from backend.utils.logger import logger
from collections import defaultdict

class TrialBalanceGenerator:
    """
    Service for generating Trial Balance reports.
    
    Generates:
    - Ledger-wise debit and credit totals
    - Opening balances
    - Closing balances
    - Balance verification (Total Debits = Total Credits)
    """

    def generate_trial_balance(self, client_id: str, year: int) -> TrialBalance:
        """
        Generate Trial Balance for a financial year.
        """
        try:
            # Financial year: April to March
            start_date = f"{year}-04-01"
            end_date = f"{year+1}-03-31"
            
            # Get opening balances (transactions before start date)
            opening_balances = self._get_opening_balances(client_id, start_date)
            
            # Fetch all transactions for the year
            response = supabase.table("transactions").select("*").eq("client_id", client_id).gte("date", start_date).lte("date", end_date).is_("deleted_at", "null").execute()
            transactions = response.data if response.data else []
            
            # Calculate ledger totals
            ledger_data = self._calculate_ledger_totals(transactions, opening_balances)
            
            # Calculate grand totals
            total_debits = sum(item["debit"] for item in ledger_data)
            total_credits = sum(item["credit"] for item in ledger_data)
            
            # Check if balanced (allowing for small rounding errors)
            is_balanced = abs(total_debits - total_credits) < 0.01
            
            return TrialBalance(
                accounts=ledger_data,
                total_debits=round(total_debits, 2),
                total_credits=round(total_credits, 2),
                is_balanced=is_balanced
            )
            
        except Exception as e:
            logger.error(f"Trial balance generation failed: {e}")
            return TrialBalance(
                accounts=[],
                total_debits=0.0,
                total_credits=0.0,
                is_balanced=True
            )

    def _get_opening_balances(self, client_id: str, start_date: str) -> Dict[str, float]:
        """
        Get opening balances for all ledgers (transactions before start date).
        """
        try:
            response = supabase.table("transactions").select("*").eq("client_id", client_id).lt("date", start_date).is_("deleted_at", "null").execute()
            
            transactions = response.data if response.data else []
            
            balances = defaultdict(float)
            
            for txn in transactions:
                ledger = txn.get("ledger", "Uncategorized")
                amount = float(txn.get("amount", 0))
                txn_type = txn.get("type", "")
                
                # Debit increases balance, Credit decreases balance
                if txn_type == "debit":
                    balances[ledger] += amount
                else:
                    balances[ledger] -= amount
            
            return dict(balances)
            
        except Exception as e:
            logger.error(f"Failed to get opening balances: {e}")
            return {}

    def _calculate_ledger_totals(self, transactions: List[Dict[str, Any]], opening_balances: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Calculate debit and credit totals per ledger with opening and closing balances.
        """
        ledger_totals = defaultdict(lambda: {
            "opening_balance": 0.0,
            "debit": 0.0,
            "credit": 0.0,
            "closing_balance": 0.0
        })
        
        # Set opening balances
        for ledger, balance in opening_balances.items():
            ledger_totals[ledger]["opening_balance"] = balance
        
        # Sum debits and credits for the period
        for txn in transactions:
            ledger = txn.get("ledger", "Uncategorized")
            amount = float(txn.get("amount", 0))
            txn_type = txn.get("type", "")
            
            if txn_type == "debit":
                ledger_totals[ledger]["debit"] += amount
            else:
                ledger_totals[ledger]["credit"] += amount
        
        # Calculate closing balances
        result = []
        for ledger, data in ledger_totals.items():
            opening = data["opening_balance"]
            debit = data["debit"]
            credit = data["credit"]
            closing = opening + debit - credit
            
            result.append({
                "ledger": ledger,
                "opening_balance": round(opening, 2),
                "debit": round(debit, 2),
                "credit": round(credit, 2),
                "closing_balance": round(closing, 2)
            })
        
        # Sort by ledger name
        result.sort(key=lambda x: x["ledger"])
        
        return result
