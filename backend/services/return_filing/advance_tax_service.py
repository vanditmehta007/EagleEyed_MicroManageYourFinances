# backend/services/return_filing/advance_tax_service.py

from typing import Dict, Any, List
from datetime import datetime
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger

class AdvanceTaxService:
    """
    Service for calculating advance tax liability and generating payment schedules.
    
    Calculates:
    - Estimated annual income
    - Advance tax liability
    - Quarterly payment schedule
    - Interest on late payment
    """

    def __init__(self) -> None:
        # TODO: Initialize database connection
        # Supabase client is imported globally
        pass

    def calculate_advance_tax(self, client_id: str, financial_year: int) -> Dict[str, Any]:
        """
        Calculate advance tax liability for a financial year.
        
        Args:
            client_id: Client identifier.
            financial_year: Financial year (e.g., 2024 for FY 2024-25).
            
        Returns:
            Advance tax calculation dict with quarterly schedule.
        """
        try:
            # TODO: Estimate annual income based on current data
            estimated_income = self._estimate_annual_income(client_id, financial_year)
            
            # TODO: Calculate tax liability
            # Simplified tax calculation (flat 25% for corporate/business assumption)
            # In production, this needs a full tax engine with slabs/deductions
            tax_rate = 0.25
            estimated_tax_liability = estimated_income * tax_rate
            
            # Check if advance tax is applicable (Liability >= 10,000)
            is_applicable = estimated_tax_liability >= 10000
            
            # TODO: Generate quarterly payment schedule
            schedule = self._calculate_quarterly_schedule(estimated_tax_liability, financial_year)
            
            # TODO: Return advance tax dict
            return {
                "client_id": client_id,
                "financial_year": f"{financial_year}-{financial_year+1}",
                "estimated_annual_income": round(estimated_income, 2),
                "estimated_tax_liability": round(estimated_tax_liability, 2),
                "is_advance_tax_applicable": is_applicable,
                "payment_schedule": schedule,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Advance tax calculation failed: {e}")
            return {"error": str(e)}

    def _estimate_annual_income(self, client_id: str, year: int) -> float:
        """
        Estimate annual income based on current year data.
        
        Args:
            client_id: Client identifier.
            year: Financial year.
            
        Returns:
            Estimated annual income.
        """
        try:
            start_date = f"{year}-04-01"
            today = datetime.utcnow()
            current_date_str = today.strftime("%Y-%m-%d")
            
            # If we are past the financial year, use full year data
            if today.year > year + 1 or (today.year == year + 1 and today.month > 3):
                end_date = f"{year+1}-03-31"
                days_elapsed = 365
            else:
                end_date = current_date_str
                days_elapsed = (today - datetime(year, 4, 1)).days
                if days_elapsed <= 0:
                    days_elapsed = 1  # Avoid division by zero
            
            # TODO: Fetch year-to-date income
            # Fetch credit transactions (Income)
            income_response = supabase.table("transactions").select("amount").eq("client_id", client_id).eq("type", "credit").gte("date", start_date).lte("date", end_date).is_("deleted_at", "null").execute()
            total_income = sum(float(t["amount"]) for t in income_response.data or [])
            
            # Fetch debit transactions (Expenses)
            expense_response = supabase.table("transactions").select("amount").eq("client_id", client_id).eq("type", "debit").gte("date", start_date).lte("date", end_date).is_("deleted_at", "null").execute()
            total_expense = sum(float(t["amount"]) for t in expense_response.data or [])
            
            net_income_ytd = total_income - total_expense
            
            # TODO: Extrapolate to full year
            # Simple linear extrapolation
            if days_elapsed < 365:
                estimated_annual_income = (net_income_ytd / days_elapsed) * 365
            else:
                estimated_annual_income = net_income_ytd
                
            # TODO: Return estimated income
            return max(0.0, estimated_annual_income)
            
        except Exception as e:
            logger.error(f"Income estimation failed: {e}")
            return 0.0

    def _calculate_quarterly_schedule(self, total_tax: float, year: int) -> List[Dict[str, Any]]:
        """
        Generate quarterly advance tax payment schedule.
        
        Args:
            total_tax: Total annual tax liability.
            year: Financial year.
            
        Returns:
            List of quarterly payment dicts with due dates and amounts.
        """
        # TODO: Calculate quarterly amounts (15%, 45%, 75%, 100%)
        # Cumulative percentages
        installments = [
            {"percent": 0.15, "due_date": f"{year}-06-15", "label": "Q1 (15%)"},
            {"percent": 0.45, "due_date": f"{year}-09-15", "label": "Q2 (45%)"},
            {"percent": 0.75, "due_date": f"{year}-12-15", "label": "Q3 (75%)"},
            {"percent": 1.00, "due_date": f"{year+1}-03-15", "label": "Q4 (100%)"}
        ]
        
        schedule = []
        cumulative_paid = 0.0
        
        for inst in installments:
            cumulative_due = total_tax * inst["percent"]
            amount_payable = cumulative_due - cumulative_paid
            
            schedule.append({
                "installment": inst["label"],
                "due_date": inst["due_date"],
                "cumulative_percentage": int(inst["percent"] * 100),
                "cumulative_amount_due": round(cumulative_due, 2),
                "payable_this_quarter": round(amount_payable, 2)
            })
            
            cumulative_paid = cumulative_due
            
        # TODO: Return quarterly schedule list
        return schedule
