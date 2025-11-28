# backend/services/report_engine/cashflow_report.py

from typing import Dict, Any, List
from datetime import datetime
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger

class CashflowGenerator:
    """
    Service for generating Cashflow Statements.
    
    Calculates:
    - Cash Flow from Operating Activities (Net Income + Adjustments)
    - Cash Flow from Investing Activities (Asset purchases/sales)
    - Cash Flow from Financing Activities (Loans, Equity)
    - Net Cash Flow
    """

    def generate_cashflow(self, client_id: str, year: int) -> Dict[str, Any]:
        """
        Generate Cashflow Statement for a specific financial year.
        
        Args:
            client_id: Client identifier.
            year: Financial year (e.g., 2024 for FY 2024-25).
            
        Returns:
            Dict containing detailed cashflow components.
        """
        try:
            start_date = f"{year}-04-01"
            end_date = f"{year+1}-03-31"
            
            # Fetch all transactions for the period
            response = supabase.table("transactions").select("*").eq("client_id", client_id).gte("date", start_date).lte("date", end_date).is_("deleted_at", "null").execute()
            transactions = response.data or []
            
            # 1. Operating Activities
            operating_inflow = 0.0
            operating_outflow = 0.0
            
            # 2. Investing Activities
            investing_inflow = 0.0
            investing_outflow = 0.0
            
            # 3. Financing Activities
            financing_inflow = 0.0
            financing_outflow = 0.0
            
            # Categorize transactions
            # Note: This relies on 'ledger' or 'category' field being populated correctly
            for txn in transactions:
                amount = float(txn.get("amount", 0))
                category = txn.get("ledger", "").lower()
                txn_type = txn.get("type", "").lower()  # credit/debit
                
                # Investing Keywords
                if any(k in category for k in ["asset", "equipment", "machinery", "investment", "property"]):
                    if txn_type == "debit":
                        investing_outflow += amount
                    else:
                        investing_inflow += amount
                        
                # Financing Keywords
                elif any(k in category for k in ["loan", "equity", "capital", "dividend", "interest"]):
                    if txn_type == "debit":
                        financing_outflow += amount
                    else:
                        financing_inflow += amount
                        
                # Operating (Default)
                else:
                    if txn_type == "debit":
                        operating_outflow += amount
                    else:
                        operating_inflow += amount
            
            # Calculate Nets
            net_operating = operating_inflow - operating_outflow
            net_investing = investing_inflow - investing_outflow
            net_financing = financing_inflow - financing_outflow
            net_cash_flow = net_operating + net_investing + net_financing
            
            return {
                "client_id": client_id,
                "financial_year": f"{year}-{year+1}",
                "generated_at": datetime.utcnow().isoformat(),
                "summary": {
                    "net_cash_from_operating": round(net_operating, 2),
                    "net_cash_from_investing": round(net_investing, 2),
                    "net_cash_from_financing": round(net_financing, 2),
                    "net_increase_decrease_in_cash": round(net_cash_flow, 2)
                },
                "details": {
                    "operating": {
                        "inflow": round(operating_inflow, 2),
                        "outflow": round(operating_outflow, 2)
                    },
                    "investing": {
                        "inflow": round(investing_inflow, 2),
                        "outflow": round(investing_outflow, 2)
                    },
                    "financing": {
                        "inflow": round(financing_inflow, 2),
                        "outflow": round(financing_outflow, 2)
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate cashflow report: {e}")
            return {
                "error": str(e),
                "operating_activities": 0,
                "investing_activities": 0,
                "financing_activities": 0,
                "net_cash_flow": 0
            }
