from typing import List, Dict, Any
from backend.models.compliance_models import GSTComplianceResult
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger

class GSTComplianceService:
    """
    Service for GST compliance checks (ITC eligibility, RCM, GSTR-2B reconciliation).
    """

    def __init__(self):
        # Section 17(5) blocked credit categories
        self.blocked_itc_keywords = [
            "food", "beverage", "outdoor catering", "beauty treatment",
            "health services", "cosmetic", "plastic surgery",
            "membership", "club", "health club", "fitness"
        ]
        
        # RCM applicable services (Section 9(3))
        self.rcm_service_keywords = [
            "legal", "advocate", "ca", "chartered accountant",
            "company secretary", "cost accountant", "architect",
            "interior decorator", "technical testing", "security",
            "manpower", "labour", "contract labour"
        ]

    def check_compliance(self, transaction_ids: List[str]) -> List[GSTComplianceResult]:
        """
        Run GST compliance checks on a list of transactions.
        """
        results = []
        
        if not transaction_ids:
            return results
        
        try:
            # Fetch transactions from database
            response = supabase.table("transactions").select("*").in_("id", transaction_ids).execute()
            transactions = response.data if response.data else []
            
            for txn in transactions:
                result = self._check_transaction_compliance(txn)
                results.append(result)
            
        except Exception as e:
            logger.error(f"GST compliance check failed: {e}")
        
        return results

    def _check_transaction_compliance(self, txn: Dict[str, Any]) -> GSTComplianceResult:
        """
        Check GST compliance for a single transaction.
        """
        itc_eligible = True
        rcm_applicable = False
        mismatch_reason = None
        law_reference = None
        
        description = str(txn.get("description", "")).lower()
        ledger = str(txn.get("ledger", "")).lower()
        amount = float(txn.get("amount", 0))
        gstin = txn.get("gstin")
        txn_type = txn.get("type", "")
        
        # Only check for expense/purchase transactions
        if txn_type != "debit":
            return GSTComplianceResult(
                transaction_id=txn.get("id", ""),
                itc_eligible=False,
                rcm_applicable=False,
                mismatch_reason="Not an expense transaction",
                law_reference=None
            )
        
        # Check Section 17(5) blocked credits
        for blocked_keyword in self.blocked_itc_keywords:
            if blocked_keyword in description or blocked_keyword in ledger:
                itc_eligible = False
                mismatch_reason = f"ITC blocked under Section 17(5) - {blocked_keyword}"
                law_reference = "CGST Act, 2017 - Section 17(5)"
                break
        
        # Check if GSTIN is missing for B2B transactions
        if itc_eligible and amount > 0:
            if not gstin or len(str(gstin).strip()) != 15:
                itc_eligible = False
                mismatch_reason = "Missing or invalid GSTIN - ITC cannot be claimed"
                law_reference = "CGST Act, 2017 - Section 16(2)(b)"
        
        # Check RCM applicability (Section 9(3))
        if not gstin or len(str(gstin).strip()) != 15:
            # Vendor is unregistered
            for rcm_keyword in self.rcm_service_keywords:
                if rcm_keyword in description or rcm_keyword in ledger:
                    rcm_applicable = True
                    if not mismatch_reason:
                        mismatch_reason = f"RCM applicable - {rcm_keyword} service from unregistered vendor"
                    if not law_reference:
                        law_reference = "CGST Act, 2017 - Section 9(3)"
                    break
        
        return GSTComplianceResult(
            transaction_id=txn.get("id", ""),
            itc_eligible=itc_eligible,
            rcm_applicable=rcm_applicable,
            mismatch_reason=mismatch_reason,
            law_reference=law_reference
        )

    def reconcile_gstr2b(self, client_id: str, month: int, year: int) -> Dict[str, Any]:
        """
        Reconcile purchase register with GSTR-2B data.
        """
        try:
            # Fetch purchase transactions for the month
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{month+1:02d}-01"
            
            # Fetch all purchase (debit) transactions
            response = supabase.table("transactions").select("*").eq("client_id", client_id).eq("type", "debit").gte("date", start_date).lt("date", end_date).is_("deleted_at", "null").execute()
            all_purchase_txns = response.data if response.data else []
            
            # Categorize transactions
            b2b_txns = []
            b2c_txns = []
            blocked_itc_txns = []
            
            total_itc_eligible = 0.0
            total_itc_blocked = 0.0
            
            for txn in all_purchase_txns:
                gstin = txn.get("gstin")
                amount = float(txn.get("amount", 0))
                
                # Estimate GST amount (18% default)
                gst_amount = float(txn.get("gst_amount", 0))
                if gst_amount == 0 and amount > 0:
                    gst_amount = amount * 18 / 118
                
                if gstin and len(str(gstin).strip()) == 15:
                    compliance_result = self._check_transaction_compliance(txn)
                    
                    if compliance_result.itc_eligible:
                        b2b_txns.append(txn)
                        total_itc_eligible += gst_amount
                    else:
                        blocked_itc_txns.append(txn)
                        total_itc_blocked += gst_amount
                else:
                    b2c_txns.append(txn)
            
            # USER INPUT REQUIRED: In production, fetch GSTR-2B from external API (e.g., ClearTax, GST Portal)
            # Example: gstr2b_data = gst_api_client.fetch_gstr2b(client_id, month, year)
            # For now, we return the purchase register analysis
            
            summary = {
                "month": month,
                "year": year,
                "period": f"{year}-{month:02d}",
                "purchase_register": {
                    "total_purchases": len(all_purchase_txns),
                    "b2b_purchases": len(b2b_txns),
                    "b2c_purchases": len(b2c_txns),
                    "blocked_itc_purchases": len(blocked_itc_txns),
                    "total_itc_eligible": round(total_itc_eligible, 2),
                    "total_itc_blocked": round(total_itc_blocked, 2)
                },
                "status": "analyzed_books_only",
                "message": "Purchase register analyzed. Connect GSTR-2B source for full reconciliation."
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"GSTR-2B reconciliation failed: {e}")
            return {"error": str(e)}
