from typing import Dict, Any
from backend.models.return_filing_models import GSTR1Summary
from backend.utils.supabase_client import supabase

class GSTR1Service:
    """
    Service for preparing GSTR-1 (Outward Supplies) summary.
    """

    def prepare_gstr1(self, client_id: str, month: int, year: int) -> GSTR1Summary:
        """
        Prepare GSTR-1 summary for a specific month and year.
        
        Args:
            client_id: Client identifier.
            month: Month (1-12).
            year: Year.
            
        Returns:
            GSTR1Summary object with outward supply details.
        """
        try:
            # Fetch all credit transactions (outward supplies) for the month
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year}-12-31"
            else:
                end_date = f"{year}-{month+1:02d}-01"
            
            response = supabase.table("transactions").select("*").eq("client_id", client_id).eq("type", "credit").gte("date", start_date).lt("date", end_date).execute()
            transactions = response.data if response.data else []
            
            total_taxable = 0.0
            b2b = 0.0
            b2c = 0.0
            exports = 0.0
            nil_rated = 0.0
            
            for txn in transactions:
                amount = float(txn.get("amount", 0))
                gstin = txn.get("gstin")
                description = txn.get("description", "").lower()
                
                # Classify supply type
                if "export" in description or "foreign" in description:
                    exports += amount
                elif gstin:
                    # B2B transaction (has GSTIN)
                    b2b += amount
                    total_taxable += amount
                elif "nil" in description or "exempt" in description:
                    nil_rated += amount
                else:
                    # B2C transaction
                    b2c += amount
                    total_taxable += amount
            
            return GSTR1Summary(
                total_taxable=round(total_taxable, 2),
                b2b=round(b2b, 2),
                b2c=round(b2c, 2),
                exports=round(exports, 2),
                nil_rated=round(nil_rated, 2)
            )
            
        except Exception as e:
            # Return default values on error
            return GSTR1Summary(
                total_taxable=0.0,
                b2b=0.0,
                b2c=0.0,
                exports=0.0,
                nil_rated=0.0
            )

