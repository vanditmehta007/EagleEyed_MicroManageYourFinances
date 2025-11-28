from typing import Dict, Any, List
from backend.models.return_filing_models import TDSSummary
from backend.utils.supabase_client import supabase

class TDSSummaryService:
    """
    Service for generating TDS return summary.
    """

    def generate_summary(self, client_id: str, quarter: int, year: int) -> TDSSummary:
        """
        Generate TDS summary for a specific quarter and year.
        
        Args:
            client_id: Client identifier.
            quarter: Quarter (1-4).
            year: Year.
            
        Returns:
            TDSSummary object with TDS details.
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
            
            # Fetch transactions with TDS applicable
            response = supabase.table("transactions").select("*").eq("client_id", client_id).eq("tds_applicable", True).gte("date", start_date).lt("date", end_date).execute()
            transactions = response.data if response.data else []
            
            # Group by vendor and calculate TDS
            vendor_breakdown = {}
            total_tds = 0.0
            
            for txn in transactions:
                vendor = txn.get("vendor", "Unknown")
                amount = float(txn.get("amount", 0))
                section = txn.get("tds_section", "194J")  # Default section
                
                # TDS rates (simplified - actual rates vary by section)
                tds_rates = {
                    "194J": 0.10,  # 10% for professional services
                    "194I": 0.10,  # 10% for rent
                    "194C": 0.01,  # 1% for contractors
                }
                rate = tds_rates.get(section, 0.10)
                tds_amount = amount * rate
                
                if vendor not in vendor_breakdown:
                    vendor_breakdown[vendor] = {
                        "vendor_name": vendor,
                        "pan": txn.get("pan", ""),
                        "total_amount": 0.0,
                        "tds_amount": 0.0,
                        "section": section
                    }
                
                vendor_breakdown[vendor]["total_amount"] += amount
                vendor_breakdown[vendor]["tds_amount"] += tds_amount
                total_tds += tds_amount
            
            # Convert to list format
            vendor_list = list(vendor_breakdown.values())
            for vendor_data in vendor_list:
                vendor_data["total_amount"] = round(vendor_data["total_amount"], 2)
                vendor_data["tds_amount"] = round(vendor_data["tds_amount"], 2)
            
            return TDSSummary(
                total_tds=round(total_tds, 2),
                vendor_breakdown=vendor_list
            )
            
        except Exception as e:
            # Return default values on error
            return TDSSummary(
                total_tds=0.0,
                vendor_breakdown=[]
            )

