# backend/services/return_filing/tds_return_service.py

from typing import Dict, Any, List
from datetime import datetime
from collections import defaultdict
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger

class TDSReturnService:
    """
    Service for generating TDS return data (Form 26Q, 27Q, etc.).
    
    Generates:
    - Deductor details
    - Deductee details
    - TDS deducted summary
    - Challan details
    """

    def __init__(self) -> None:
        # TODO: Initialize database connection
        # Supabase client is imported globally
        pass

    def generate_tds_return(self, client_id: str, quarter: str, year: int) -> Dict[str, Any]:
        """
        Generate TDS return data for a quarter.
        
        Args:
            client_id: Client identifier.
            quarter: Quarter (Q1, Q2, Q3, Q4).
            year: Financial year (e.g., 2024 for FY 2024-25).
            
        Returns:
            TDS return data dict.
        """
        try:
            # Determine date range for the quarter
            quarter_map = {
                "Q1": (f"{year}-04-01", f"{year}-06-30"),
                "Q2": (f"{year}-07-01", f"{year}-09-30"),
                "Q3": (f"{year}-10-01", f"{year}-12-31"),
                "Q4": (f"{year+1}-01-01", f"{year+1}-03-31")
            }
            
            if quarter not in quarter_map:
                raise ValueError("Invalid quarter. Must be Q1, Q2, Q3, or Q4.")
                
            start_date, end_date = quarter_map[quarter]
            
            # TODO: Fetch all TDS transactions for the quarter
            # Fetch debit transactions (Expenses) where TDS is applicable
            # Assuming 'tds_amount' > 0 or specific flag indicates TDS
            response = supabase.table("transactions").select("*").eq("client_id", client_id).gte("date", start_date).lte("date", end_date).gt("tds_amount", 0).is_("deleted_at", "null").execute()
            transactions = response.data or []
            
            # TODO: Group by deductee
            deductee_summary = self._get_deductee_summary(transactions)
            
            # TODO: Calculate TDS amounts per section
            section_summary = self._get_section_summary(transactions)
            
            # TODO: Format according to TDS return schema
            tds_return_data = {
                "deductor": self._get_deductor_details(client_id),
                "return_period": {
                    "quarter": quarter,
                    "financial_year": f"{year}-{year+1}"
                },
                "deductee_details": deductee_summary,
                "section_summary": section_summary,
                "total_tds_deducted": sum(float(t.get("tds_amount", 0)) for t in transactions),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # TODO: Return TDS return dict
            return tds_return_data
            
        except Exception as e:
            logger.error(f"TDS return generation failed: {e}")
            return {"error": str(e)}

    def _get_deductor_details(self, client_id: str) -> Dict[str, Any]:
        """
        Get deductor (client) details.
        """
        try:
            # TODO: Fetch client details (PAN, TAN, name, address)
            response = supabase.table("clients").select("name, pan, tan, address").eq("id", client_id).single().execute()
            if response.data:
                return response.data
            return {"name": "Unknown", "pan": "", "tan": "", "address": ""}
        except Exception as e:
            logger.error(f"Failed to fetch deductor details: {e}")
            return {}

    def _get_deductee_summary(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get deductee-wise TDS summary.
        """
        # TODO: Group transactions by deductee (vendor)
        grouped = defaultdict(lambda: {"total_amount": 0.0, "tds_deducted": 0.0, "pan": ""})
        
        for txn in transactions:
            vendor = txn.get("vendor", "Unknown")
            # Assuming vendor PAN is stored in transaction or can be looked up
            # Using placeholder for now
            pan = txn.get("vendor_pan", "PANNOTAVAIL") 
            
            amount = float(txn.get("amount", 0))
            tds = float(txn.get("tds_amount", 0))
            
            grouped[vendor]["total_amount"] += amount
            grouped[vendor]["tds_deducted"] += tds
            grouped[vendor]["pan"] = pan
            
        # TODO: Sum TDS amounts per deductee
        summary_list = []
        for vendor, data in grouped.items():
            summary_list.append({
                "deductee_name": vendor,
                "deductee_pan": data["pan"],
                "total_amount_paid": round(data["total_amount"], 2),
                "total_tds_deducted": round(data["tds_deducted"], 2)
            })
            
        # TODO: Return deductee summary list
        return summary_list

    def _get_section_summary(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get section-wise TDS summary (e.g., 194C, 194J).
        """
        grouped = defaultdict(lambda: {"count": 0, "tds_amount": 0.0})
        
        for txn in transactions:
            # Assuming 'tds_section' field exists, e.g., "194C"
            section = txn.get("tds_section", "Unknown")
            tds = float(txn.get("tds_amount", 0))
            
            grouped[section]["count"] += 1
            grouped[section]["tds_amount"] += tds
            
        summary_list = []
        for section, data in grouped.items():
            summary_list.append({
                "section_code": section,
                "transaction_count": data["count"],
                "total_tds": round(data["tds_amount"], 2)
            })
            
        return summary_list
