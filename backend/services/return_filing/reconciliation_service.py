# backend/services/return_filing/reconciliation_service.py

from typing import Dict, Any, List
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger

class ReconciliationService:
    """
    Service for reconciling books with GST returns (GSTR-2A/2B vs books).
    
    Performs:
    - GSTR-2A/2B reconciliation
    - ITC mismatch detection
    - Missing invoice identification
    - Excess ITC claims
    """

    def __init__(self) -> None:
        # Supabase client is imported globally
        pass

    def reconcile(self, client_id: str, month: int, year: int) -> Dict[str, Any]:
        """
        Reconcile books with GSTR-2B data.
        
        Args:
            client_id: Client identifier.
            month: Month (1-12).
            year: Year (e.g., 2024).
            
        Returns:
            Reconciliation report dict with matches, mismatches, and missing invoices.
        """
        try:
            # Fetch book entries for the period
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{month+1:02d}-01"
            
            response = supabase.table("transactions").select("*").eq("client_id", client_id).eq("type", "debit").gte("date", start_date).lt("date", end_date).is_("deleted_at", "null").execute()
            book_entries = response.data if response.data else []
            
            # USER INPUT REQUIRED: Simulate GSTR-2B data fetch (In production, fetch from GST API)
            # For now, we'll assume GSTR-2B data is stored in a 'gstr_data' table or passed in
            # This is a placeholder simulation
            gstr2b_entries = [] # Placeholder: fetch_gstr2b_data(client_id, month, year)
            
            # Perform matching
            match_result = self._match_invoices(book_entries, gstr2b_entries)
            
            # Identify mismatches in matched pairs
            mismatches = self._identify_mismatches(match_result["matched_pairs"])
            
            return {
                "client_id": client_id,
                "month": month,
                "year": year,
                "total_book_entries": len(book_entries),
                "total_gstr2b_entries": len(gstr2b_entries),
                "matched_count": len(match_result["matched_pairs"]),
                "unmatched_in_books": len(match_result["unmatched_books"]),
                "unmatched_in_gstr2b": len(match_result["unmatched_gstr2b"]),
                "mismatched_count": len(mismatches),
                "details": {
                    "matched": match_result["matched_pairs"],
                    "unmatched_books": match_result["unmatched_books"],
                    "unmatched_gstr2b": match_result["unmatched_gstr2b"],
                    "mismatches": mismatches
                }
            }
            
        except Exception as e:
            logger.error(f"Reconciliation failed: {e}")
            return {"error": str(e)}

    def _match_invoices(self, book_entries: List[Dict[str, Any]], gstr2b_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Match invoices between books and GSTR-2B.
        """
        matched_pairs = []
        unmatched_books = []
        unmatched_gstr2b = list(gstr2b_entries) # Start with all, remove as we match
        
        # Index GSTR-2B entries by (GSTIN, Invoice Number) for O(1) lookup
        gstr_map = {}
        for entry in gstr2b_entries:
            key = (entry.get("ctin"), entry.get("inum")) # ctin=GSTIN, inum=Invoice Num
            gstr_map[key] = entry
            
        for book_entry in book_entries:
            gstin = book_entry.get("gstin")
            inv_num = book_entry.get("invoice_number")
            
            if gstin and inv_num:
                key = (gstin, inv_num)
                if key in gstr_map:
                    gstr_entry = gstr_map[key]
                    matched_pairs.append({
                        "book": book_entry,
                        "gstr2b": gstr_entry
                    })
                    if gstr_entry in unmatched_gstr2b:
                        unmatched_gstr2b.remove(gstr_entry)
                else:
                    unmatched_books.append(book_entry)
            else:
                unmatched_books.append(book_entry)
                
        return {
            "matched_pairs": matched_pairs,
            "unmatched_books": unmatched_books,
            "unmatched_gstr2b": unmatched_gstr2b
        }

    def _identify_mismatches(self, matched_pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify mismatches in matched invoice pairs.
        """
        mismatches = []
        
        for pair in matched_pairs:
            book = pair["book"]
            gstr = pair["gstr2b"]
            
            issues = []
            
            # Compare Taxable Value
            book_val = float(book.get("amount", 0)) # Assuming amount is taxable for simplicity, or extract taxable
            gstr_val = float(gstr.get("val", 0))
            
            if abs(book_val - gstr_val) > 1.0: # Allow small rounding diff
                issues.append(f"Taxable Value Mismatch: Book {book_val} vs GSTR {gstr_val}")
                
            # Compare Tax Amounts (IGST/CGST/SGST)
            # Placeholder logic
            
            if issues:
                mismatches.append({
                    "invoice_number": book.get("invoice_number"),
                    "gstin": book.get("gstin"),
                    "issues": issues
                })
                
        return mismatches
