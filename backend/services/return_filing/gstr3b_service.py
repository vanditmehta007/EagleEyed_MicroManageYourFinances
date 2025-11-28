# backend/services/return_filing/gstr3b_service.py

from typing import Dict, Any, List
from datetime import datetime
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger

class GSTR3BService:
    """
    Service for generating GSTR-3B (summary return) data.
    
    Generates:
    - Outward supplies summary (Table 3.1)
    - Inward supplies (ITC) summary (Table 4)
    - Tax liability
    - ITC claimed
    - Tax paid
    """

    def __init__(self) -> None:
        # TODO: Initialize database connection
        # Supabase client is imported globally
        pass

    def generate_gstr3b(self, client_id: str, month: str, year: int) -> Dict[str, Any]:
        """
        Generate GSTR-3B return data for a month.
        
        Args:
            client_id: Client identifier.
            month: Month (01-12).
            year: Year (e.g., 2024).
            
        Returns:
            GSTR-3B data dict in GST portal format.
        """
        try:
            # Calculate date range
            start_date = f"{year}-{month}-01"
            if int(month) == 12:
                next_month = f"{year+1}-01-01"
            else:
                next_month = f"{year}-{int(month)+1:02d}-01"
            
            # TODO: Fetch all transactions for the period
            # Fetch Outward Supplies (Credit/Sales)
            outward_response = supabase.table("transactions").select("*").eq("client_id", client_id).eq("type", "credit").gte("date", start_date).lt("date", next_month).is_("deleted_at", "null").execute()
            outward_txns = outward_response.data or []
            
            # Fetch Inward Supplies (Debit/Purchases)
            inward_response = supabase.table("transactions").select("*").eq("client_id", client_id).eq("type", "debit").gte("date", start_date).lt("date", next_month).is_("deleted_at", "null").execute()
            inward_txns = inward_response.data or []
            
            # TODO: Calculate outward supplies summary
            outward_summary = self._calculate_outward_supplies(outward_txns)
            
            # TODO: Calculate ITC summary
            itc_summary = self._calculate_itc(inward_txns)
            
            # TODO: Calculate tax liability
            liability = self._calculate_tax_liability(outward_summary, itc_summary)
            
            # TODO: Format according to GST portal JSON schema
            gstr3b_data = {
                "gstin": "CLIENT_GSTIN_PLACEHOLDER",
                "ret_period": f"{month}{year}",
                "sup_details": {
                    "osup_det": {
                        "txval": outward_summary["taxable_value"],
                        "iamt": outward_summary["igst"],
                        "camt": outward_summary["cgst"],
                        "samt": outward_summary["sgst"],
                        "csamt": 0
                    }
                },
                "itc_elg": {
                    "itc_avl": [
                        {
                            "ty": "ALL",
                            "iamt": itc_summary["igst"],
                            "camt": itc_summary["cgst"],
                            "samt": itc_summary["sgst"],
                            "csamt": 0
                        }
                    ]
                },
                "tax_liability": liability,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # TODO: Return GSTR-3B dict
            return gstr3b_data
            
        except Exception as e:
            logger.error(f"GSTR-3B generation failed: {e}")
            return {"error": str(e)}

    def _calculate_outward_supplies(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate outward supplies summary.
        """
        summary = {"taxable_value": 0.0, "igst": 0.0, "cgst": 0.0, "sgst": 0.0}
        
        # TODO: Sum taxable value and tax amounts
        for txn in transactions:
            amount = float(txn.get("amount", 0))
            # Assuming 18% GST default
            tax_rate = 18.0
            taxable = round(amount / (1 + tax_rate/100), 2)
            tax = round(amount - taxable, 2)
            
            summary["taxable_value"] += taxable
            
            # Simplified logic: If POS != Client State -> IGST, else CGST+SGST
            # For now, assuming 50% IGST and 50% Intra-state for placeholder logic
            # In real app, check POS code
            if txn.get("gstin", "").startswith("27"): # Example: Maharashtra
                 summary["cgst"] += tax / 2
                 summary["sgst"] += tax / 2
            else:
                 summary["igst"] += tax
                 
        # Round final values
        summary = {k: round(v, 2) for k, v in summary.items()}
        
        # TODO: Return summary dict
        return summary

    def _calculate_itc(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate Input Tax Credit summary.
        """
        summary = {"igst": 0.0, "cgst": 0.0, "sgst": 0.0}
        
        # TODO: Sum eligible ITC amounts
        for txn in transactions:
            # Only consider transactions with GSTIN (B2B purchases)
            if txn.get("gstin"):
                amount = float(txn.get("amount", 0))
                tax_rate = 18.0
                taxable = round(amount / (1 + tax_rate/100), 2)
                tax = round(amount - taxable, 2)
                
                # Simplified logic similar to outward
                if txn.get("gstin", "").startswith("27"):
                    summary["cgst"] += tax / 2
                    summary["sgst"] += tax / 2
                else:
                    summary["igst"] += tax
                    
        summary = {k: round(v, 2) for k, v in summary.items()}
        
        # TODO: Return ITC summary dict
        return summary

    def _calculate_tax_liability(self, outward: Dict[str, Any], itc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate net tax liability.
        """
        # TODO: Calculate net tax (outward tax - ITC)
        net_igst = max(0, outward["igst"] - itc["igst"])
        net_cgst = max(0, outward["cgst"] - itc["cgst"])
        net_sgst = max(0, outward["sgst"] - itc["sgst"])
        
        # TODO: Return tax liability dict
        return {
            "net_tax_payable": {
                "igst": round(net_igst, 2),
                "cgst": round(net_cgst, 2),
                "sgst": round(net_sgst, 2)
            },
            "total_payable": round(net_igst + net_cgst + net_sgst, 2)
        }
