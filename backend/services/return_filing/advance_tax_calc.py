from typing import Dict, Any
from backend.utils.supabase_client import supabase

class AdvanceTaxService:
    """
    Service for calculating Advance Tax liability.
    """

    def calculate_tax(self, client_id: str, quarter: int, year: int) -> Dict[str, Any]:
        """
        Calculate Advance Tax liability for a specific quarter.
        
        Args:
            client_id: Client identifier.
            quarter: Quarter (1-4).
            year: Year.
            
        Returns:
            Dictionary with advance tax calculation details.
        """
        try:
            # Calculate quarter date range
            quarter_months = {
                1: (1, 3),
                2: (4, 6),
                3: (7, 9),
                4: (10, 12)
            }
            start_month, end_month = quarter_months.get(quarter, (1, 3))
            start_date = f"{year}-{start_month:02d}-01"
            if end_month == 12:
                end_date = f"{year}-12-31"
            else:
                end_date = f"{year}-{end_month+1:02d}-01"
            
            # Fetch all transactions for the quarter
            response = supabase.table("transactions").select("*").eq("client_id", client_id).gte("date", start_date).lt("date", end_date).execute()
            transactions = response.data if response.data else []
            
            # Calculate profit (simplified: revenue - expenses)
            revenue = 0.0
            expenses = 0.0
            
            for txn in transactions:
                amount = float(txn.get("amount", 0))
                if txn.get("type") == "credit":
                    revenue += amount
                else:
                    expenses += amount
            
            profit = revenue - expenses
            
            # Estimate annual profit (extrapolate from quarter)
            estimated_annual_profit = profit * 4
            
            # Calculate tax (assuming 30% rate for companies, 30% for individuals above threshold)
            # This is simplified - actual calculation depends on entity type and tax slab
            tax_rate = 0.30
            estimated_annual_tax = estimated_annual_profit * tax_rate
            
            # Advance tax installments (as per Income Tax Act)
            # Q1: 15%, Q2: 45%, Q3: 75%, Q4: 100%
            installment_percentages = {
                1: 0.15,
                2: 0.45,
                3: 0.75,
                4: 1.00
            }
            percentage = installment_percentages.get(quarter, 0.15)
            cumulative_tax_due = estimated_annual_tax * percentage
            
            # Previous quarter payments (would be fetched from tax payments table)
            previous_payments = 0.0  # Placeholder
            
            tax_payable = cumulative_tax_due - previous_payments
            
            return {
                "quarter": quarter,
                "year": year,
                "quarter_profit": round(profit, 2),
                "estimated_annual_profit": round(estimated_annual_profit, 2),
                "estimated_annual_tax": round(estimated_annual_tax, 2),
                "cumulative_tax_due": round(cumulative_tax_due, 2),
                "previous_payments": round(previous_payments, 2),
                "tax_payable": round(max(tax_payable, 0), 2),
                "due_date": end_date
            }
            
        except Exception as e:
            # Return default values on error
            return {
                "quarter": quarter,
                "year": year,
                "quarter_profit": 0.0,
                "estimated_annual_profit": 0.0,
                "estimated_annual_tax": 0.0,
                "cumulative_tax_due": 0.0,
                "previous_payments": 0.0,
                "tax_payable": 0.0,
                "due_date": ""
            }

