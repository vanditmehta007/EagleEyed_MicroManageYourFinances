from typing import Dict, Any
from backend.models.return_filing_models import GSTR3BSummary
from backend.utils.supabase_client import supabase

class GSTR3BService:
    """
    Service for preparing GSTR-3B (Monthly Return) summary.
    """

    def prepare_gstr3b(self, client_id: str, month: int, year: int) -> GSTR3BSummary:
        """
        Prepare GSTR-3B summary for a specific month and year.
        
        Args:
            client_id: Client identifier.
            month: Month (1-12).
            year: Year.
            
        Returns:
            GSTR3BSummary object with tax liability details.
        """
        try:
            # Fetch transactions for the month
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year}-12-31"
            else:
                end_date = f"{year}-{month+1:02d}-01"
            
            # Outward supplies (credit transactions)
            outward_response = supabase.table("transactions").select("*").eq("client_id", client_id).eq("type", "credit").gte("date", start_date).lt("date", end_date).execute()
            outward_txns = outward_response.data if outward_response.data else []
            
            # Inward supplies (debit transactions)
            inward_response = supabase.table("transactions").select("*").eq("client_id", client_id).eq("type", "debit").gte("date", start_date).lt("date", end_date).execute()
            inward_txns = inward_response.data if inward_response.data else []
            
            # Calculate outward tax (on sales)
            outward_tax = 0.0
            for txn in outward_txns:
                amount = float(txn.get("amount", 0))
                if txn.get("gst_applicable"):
                    # Assuming 18% GST rate (would be configurable)
                    gst_rate = 0.18
                    tax = amount * (gst_rate / (1 + gst_rate))
                    outward_tax += tax
            
            # Calculate eligible ITC (on purchases)
            eligible_itc = 0.0
            for txn in inward_txns:
                amount = float(txn.get("amount", 0))
                gstin = txn.get("gstin")
                # ITC eligible only if vendor has GSTIN and transaction is GST applicable
                if txn.get("gst_applicable") and gstin:
                    gst_rate = 0.18
                    itc = amount * (gst_rate / (1 + gst_rate))
                    eligible_itc += itc
            
            # Calculate RCM tax (Reverse Charge Mechanism)
            rcm_tax = 0.0
            for txn in inward_txns:
                # RCM applies to services from unregistered persons
                if not txn.get("gstin") and txn.get("type") == "debit":
                    description = txn.get("description", "").lower()
                    service_keywords = ["service", "consulting", "professional", "fees"]
                    if any(keyword in description for keyword in service_keywords):
                        amount = float(txn.get("amount", 0))
                        gst_rate = 0.18
                        rcm = amount * (gst_rate / (1 + gst_rate))
                        rcm_tax += rcm
            
            # Net payable = Outward tax - ITC + RCM
            net_payable = outward_tax - eligible_itc + rcm_tax
            
            return GSTR3BSummary(
                outward_tax=round(outward_tax, 2),
                eligible_itc=round(eligible_itc, 2),
                rcm_tax=round(rcm_tax, 2),
                net_payable=round(net_payable, 2)
            )
            
        except Exception as e:
            # Return default values on error
            return GSTR3BSummary(
                outward_tax=0.0,
                eligible_itc=0.0,
                rcm_tax=0.0,
                net_payable=0.0
            )

