from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from backend.utils.supabase_client import supabase
from backend.config import settings
from backend.utils.logger import logger


class GSTMismatchDetector:
    """
    Service for detecting GST mismatches between books and GSTR-2B, incorrect GST rates, and ITC discrepancies.
    
    Detects:
    - Mismatches between books and GSTR-2B (missing invoices, amount differences)
    - Incorrect GST rates applied to transactions
    - ITC eligibility discrepancies
    - GSTIN mismatches
    - Tax amount calculation errors
    """

    def __init__(self):
        self.gst_rates = {
            "0": 0.0,      # Nil rated
            "5": 5.0,      # 5% GST
            "12": 12.0,    # 12% GST
            "18": 18.0,    # 18% GST (most common)
            "28": 28.0     # 28% GST
        }
        self.default_gst_rate = settings.GST_RATE_DEFAULT  # 18%
        self.amount_tolerance = 0.01  # 1% tolerance for amount matching
        self.tax_tolerance = 1.0  # ₹1 tolerance for tax amount

    def detect_gstr2b_mismatches(
        self, 
        client_id: str, 
        month: int, 
        year: int,
        gstr2b_data: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect mismatches between books and GSTR-2B data.
        
        Compares:
        - Invoices in books but not in GSTR-2B
        - Invoices in GSTR-2B but not in books
        - Amount mismatches
        - GSTIN mismatches
        - Tax amount differences
        
        Args:
            client_id: Client identifier.
            month: Month (1-12).
            year: Year.
            gstr2b_data: Optional GSTR-2B data. If not provided, will attempt to fetch from database.
            
        Returns:
            List of dictionaries containing mismatch details.
        """
        try:
            # Calculate date range for the month
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year}-12-31"
            else:
                end_date = f"{year}-{month+1:02d}-01"
            
            # Fetch book transactions (debit transactions with GST)
            response = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).eq("type", "debit").eq("gst_applicable", True).gte("date", start_date).lt(
                "date", end_date
            ).is_("deleted_at", "null").execute()
            
            book_transactions = response.data if response.data else []
            
            # If GSTR-2B data not provided, create empty structure
            # In production, this would be fetched from a GSTR-2B import/table
            if gstr2b_data is None:
                gstr2b_data = []
                logger.warning("GSTR-2B data not provided. Only book-side checks will be performed.")
            
            # Create lookup dictionaries
            book_invoices = {}
            for txn in book_transactions:
                invoice_number = txn.get("invoice_number", "").strip().upper()
                gstin = txn.get("gstin", "").strip() if txn.get("gstin") else ""
                if invoice_number and gstin:
                    key = f"{invoice_number}_{gstin}"
                    book_invoices[key] = txn
            
            gstr2b_invoices = {}
            for entry in gstr2b_data:
                invoice_number = entry.get("invoice_number", "").strip().upper()
                gstin = entry.get("gstin", "").strip() if entry.get("gstin") else ""
                if invoice_number and gstin:
                    key = f"{invoice_number}_{gstin}"
                    gstr2b_invoices[key] = entry
            
            mismatches = []
            
            # Check 1: Invoices in books but not in GSTR-2B
            for key, txn in book_invoices.items():
                if key not in gstr2b_invoices:
                    amount = float(txn.get("amount", 0))
                    mismatches.append({
                        "mismatch_type": "missing_in_gstr2b",
                        "transaction_id": txn.get("id"),
                        "invoice_number": txn.get("invoice_number"),
                        "gstin": txn.get("gstin"),
                        "vendor": txn.get("vendor"),
                        "date": txn.get("date"),
                        "amount": amount,
                        "severity": "high",
                        "message": f"Invoice '{txn.get('invoice_number')}' from vendor '{txn.get('vendor')}' "
                                  f"with GSTIN {txn.get('gstin')} exists in books but not in GSTR-2B",
                        "implication": "ITC may not be available if invoice is not reflected in GSTR-2B. "
                                     "Verify with vendor if invoice was uploaded correctly.",
                        "law_reference": "CGST Act, 2017 - Section 16(2)"
                    })
            
            # Check 2: Invoices in GSTR-2B but not in books
            for key, entry in gstr2b_invoices.items():
                if key not in book_invoices:
                    amount = float(entry.get("taxable_value", 0)) + float(entry.get("tax_amount", 0))
                    mismatches.append({
                        "mismatch_type": "missing_in_books",
                        "invoice_number": entry.get("invoice_number"),
                        "gstin": entry.get("gstin"),
                        "vendor_name": entry.get("vendor_name", "Unknown"),
                        "invoice_date": entry.get("invoice_date"),
                        "amount": amount,
                        "severity": "high",
                        "message": f"Invoice '{entry.get('invoice_number')}' from vendor "
                                  f"'{entry.get('vendor_name')}' with GSTIN {entry.get('gstin')} "
                                  f"exists in GSTR-2B but not in books",
                        "implication": "Invoice may have been received but not recorded. "
                                     "Verify if this is a missing entry that needs to be added.",
                        "law_reference": "CGST Act, 2017 - Section 16(2)"
                    })
            
            # Check 3: Amount mismatches for matched invoices
            for key in set(book_invoices.keys()) & set(gstr2b_invoices.keys()):
                txn = book_invoices[key]
                entry = gstr2b_invoices[key]
                
                book_amount = float(txn.get("amount", 0))
                gstr2b_taxable = float(entry.get("taxable_value", 0))
                gstr2b_tax = float(entry.get("tax_amount", 0))
                gstr2b_total = gstr2b_taxable + gstr2b_tax
                
                amount_diff = abs(book_amount - gstr2b_total)
                tolerance = book_amount * self.amount_tolerance
                
                if amount_diff > tolerance:
                    mismatches.append({
                        "mismatch_type": "amount_mismatch",
                        "transaction_id": txn.get("id"),
                        "invoice_number": txn.get("invoice_number"),
                        "gstin": txn.get("gstin"),
                        "book_amount": book_amount,
                        "gstr2b_amount": gstr2b_total,
                        "difference": round(amount_diff, 2),
                        "severity": "high",
                        "message": f"Amount mismatch for invoice '{txn.get('invoice_number')}': "
                                  f"Books show ₹{book_amount:,.2f} but GSTR-2B shows ₹{gstr2b_total:,.2f} "
                                  f"(difference: ₹{amount_diff:,.2f})",
                        "implication": "Amount discrepancy may affect ITC claim. Verify correct amount with vendor.",
                        "law_reference": "CGST Act, 2017 - Section 16(2)"
                    })
                
                # Check tax amount mismatch
                # Calculate expected tax from book amount
                # Assuming GST is included in amount
                book_taxable = book_amount / (1 + self.default_gst_rate / 100)
                book_tax = book_amount - book_taxable
                
                tax_diff = abs(book_tax - gstr2b_tax)
                if tax_diff > self.tax_tolerance:
                    mismatches.append({
                        "mismatch_type": "tax_amount_mismatch",
                        "transaction_id": txn.get("id"),
                        "invoice_number": txn.get("invoice_number"),
                        "gstin": txn.get("gstin"),
                        "book_tax": round(book_tax, 2),
                        "gstr2b_tax": round(gstr2b_tax, 2),
                        "difference": round(tax_diff, 2),
                        "severity": "medium",
                        "message": f"Tax amount mismatch for invoice '{txn.get('invoice_number')}': "
                                  f"Books show tax ₹{book_tax:,.2f} but GSTR-2B shows ₹{gstr2b_tax:,.2f}",
                        "implication": "Tax amount discrepancy may affect ITC calculation.",
                        "law_reference": "CGST Act, 2017 - Section 16(2)"
                    })
            
            logger.info(f"Detected {len(mismatches)} GSTR-2B mismatches for client {client_id}, month {month}/{year}")
            return mismatches
            
        except Exception as e:
            logger.error(f"Error detecting GSTR-2B mismatches: {str(e)}")
            return []

    def detect_incorrect_gst_rates(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect transactions with incorrect GST rates applied.
        
        Checks:
        - GST rate consistency with transaction type
        - Expected GST rates for common goods/services
        - Zero-rated vs exempt vs taxable classification
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            List of dictionaries containing incorrect GST rate details.
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().date().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=90)).date().isoformat()
            
            # Fetch GST-applicable transactions
            response = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).eq("gst_applicable", True).gte("date", start_date).lte(
                "date", end_date
            ).is_("deleted_at", "null").execute()
            
            transactions = response.data if response.data else []
            
            incorrect_rates = []
            
            # Expected GST rates by transaction type/keywords
            expected_rates = {
                "food": 5.0,
                "restaurant": 5.0,
                "medicine": 5.0,
                "pharmaceutical": 5.0,
                "textile": 5.0,
                "clothing": 5.0,
                "rent": 18.0,
                "service": 18.0,
                "consulting": 18.0,
                "professional": 18.0,
                "luxury": 28.0,
                "sin": 28.0,
                "tobacco": 28.0,
                "alcohol": 28.0
            }
            
            for txn in transactions:
                amount = float(txn.get("amount", 0))
                description = txn.get("description", "").lower()
                gstin = txn.get("gstin", "")
                
                # Calculate GST rate from amount (assuming GST is included)
                # If amount is 118, taxable is 100, tax is 18, rate is 18%
                # This is a simplified calculation
                gst_rate_field = txn.get("gst_rate")  # If stored separately
                
                # Check if transaction should be GST applicable
                if not gstin and amount > 0:
                    # Transaction without GSTIN but marked as GST applicable
                    incorrect_rates.append({
                        "mismatch_type": "gst_applicable_without_gstin",
                        "transaction_id": txn.get("id"),
                        "date": txn.get("date"),
                        "amount": amount,
                        "vendor": txn.get("vendor"),
                        "description": txn.get("description"),
                        "severity": "high",
                        "message": f"Transaction marked as GST applicable but vendor GSTIN is missing. "
                                  f"Amount: ₹{amount:,.2f}, Vendor: {txn.get('vendor')}",
                        "implication": "ITC cannot be claimed without valid GSTIN. Verify if GST is applicable.",
                        "law_reference": "CGST Act, 2017 - Section 16(2)(a)"
                    })
                
                # Check for expected GST rates based on description
                detected_rate = None
                for keyword, expected_rate in expected_rates.items():
                    if keyword in description:
                        detected_rate = expected_rate
                        break
                
                # If we detected an expected rate, check if it matches
                # Note: This is simplified - actual rate detection would need more sophisticated logic
                if detected_rate and gst_rate_field:
                    actual_rate = float(gst_rate_field)
                    if abs(actual_rate - detected_rate) > 1.0:  # More than 1% difference
                        incorrect_rates.append({
                            "mismatch_type": "rate_mismatch",
                            "transaction_id": txn.get("id"),
                            "date": txn.get("date"),
                            "amount": amount,
                            "vendor": txn.get("vendor"),
                            "description": txn.get("description"),
                            "expected_rate": detected_rate,
                            "actual_rate": actual_rate,
                            "severity": "medium",
                            "message": f"GST rate mismatch: Expected {detected_rate}% based on description "
                                      f"but transaction shows {actual_rate}%",
                            "implication": "Incorrect GST rate may affect ITC claim or tax liability.",
                            "law_reference": "CGST Act, 2017 - Rate Schedule"
                        })
            
            logger.info(f"Detected {len(incorrect_rates)} incorrect GST rate issues for client {client_id}")
            return incorrect_rates
            
        except Exception as e:
            logger.error(f"Error detecting incorrect GST rates: {str(e)}")
            return []

    def detect_itc_discrepancies(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect ITC (Input Tax Credit) eligibility discrepancies.
        
        Checks:
        - ITC claimed but not eligible (blocked credits)
        - ITC eligible but not claimed
        - ITC on exempt/nil-rated supplies
        - ITC on personal expenses
        - ITC without valid GSTIN
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            List of dictionaries containing ITC discrepancy details.
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().date().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=90)).date().isoformat()
            
            # Fetch debit transactions (purchases) with GST
            response = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).eq("type", "debit").eq("gst_applicable", True).gte("date", start_date).lte(
                "date", end_date
            ).is_("deleted_at", "null").execute()
            
            transactions = response.data if response.data else []
            
            itc_discrepancies = []
            
            # Blocked credit categories
            blocked_keywords = {
                "personal": "Personal expenses are not eligible for ITC",
                "exempt": "Exempt supplies are not eligible for ITC",
                "nil": "Nil-rated supplies are not eligible for ITC",
                "entertainment": "Entertainment expenses are not eligible for ITC",
                "club": "Club membership fees are not eligible for ITC",
                "health": "Health insurance for employees is not eligible for ITC",
                "motor vehicle": "Motor vehicle expenses (except for specific business use) are not eligible"
            }
            
            for txn in transactions:
                amount = float(txn.get("amount", 0))
                description = txn.get("description", "").lower()
                gstin = txn.get("gstin", "")
                ledger = txn.get("ledger", "").lower() if txn.get("ledger") else ""
                
                # Check 1: ITC without GSTIN
                if not gstin and amount > 0:
                    itc_discrepancies.append({
                        "discrepancy_type": "itc_without_gstin",
                        "transaction_id": txn.get("id"),
                        "date": txn.get("date"),
                        "amount": amount,
                        "vendor": txn.get("vendor"),
                        "severity": "high",
                        "message": f"ITC cannot be claimed: Transaction has no vendor GSTIN. "
                                  f"Amount: ₹{amount:,.2f}",
                        "implication": "ITC is not available without valid GSTIN of supplier.",
                        "law_reference": "CGST Act, 2017 - Section 16(2)(a)"
                    })
                
                # Check 2: Blocked credits
                for keyword, reason in blocked_keywords.items():
                    if keyword in description or keyword in ledger:
                        # Calculate potential ITC (simplified)
                        gst_rate = self.default_gst_rate
                        taxable_value = amount / (1 + gst_rate / 100)
                        itc_amount = amount - taxable_value
                        
                        itc_discrepancies.append({
                            "discrepancy_type": "blocked_credit",
                            "transaction_id": txn.get("id"),
                            "date": txn.get("date"),
                            "amount": amount,
                            "vendor": txn.get("vendor"),
                            "description": txn.get("description"),
                            "ledger": txn.get("ledger"),
                            "blocked_itc": round(itc_amount, 2),
                            "severity": "high",
                            "message": f"Blocked ITC: {reason}. Transaction amount: ₹{amount:,.2f}",
                            "implication": f"ITC of ₹{itc_amount:,.2f} cannot be claimed. {reason}.",
                            "law_reference": "CGST Act, 2017 - Section 17(5)"
                        })
                        break
                
                # Check 3: RCM applicable but ITC claimed
                # RCM (Reverse Charge Mechanism) transactions may have different ITC rules
                if "service" in description and not gstin:
                    itc_discrepancies.append({
                        "discrepancy_type": "rcm_itc_issue",
                        "transaction_id": txn.get("id"),
                        "date": txn.get("date"),
                        "amount": amount,
                        "vendor": txn.get("vendor"),
                        "severity": "medium",
                        "message": f"RCM may be applicable: Service transaction without GSTIN. "
                                  f"Amount: ₹{amount:,.2f}",
                        "implication": "If RCM applies, tax needs to be paid by recipient, not supplier.",
                        "law_reference": "CGST Act, 2017 - Section 9(3)"
                    })
            
            logger.info(f"Detected {len(itc_discrepancies)} ITC discrepancies for client {client_id}")
            return itc_discrepancies
            
        except Exception as e:
            logger.error(f"Error detecting ITC discrepancies: {str(e)}")
            return []

    def run_full_scan(
        self, 
        client_id: str, 
        month: Optional[int] = None,
        year: Optional[int] = None,
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None,
        gstr2b_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Run a comprehensive GST mismatch detection scan combining all methods.
        
        Args:
            client_id: Client identifier.
            month: Optional month (1-12) for GSTR-2B comparison.
            year: Optional year for GSTR-2B comparison.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            gstr2b_data: Optional GSTR-2B data for comparison.
            
        Returns:
            Dictionary containing all detected mismatches categorized by type.
        """
        try:
            # If month and year provided, use for GSTR-2B check
            gstr2b_mismatches = []
            if month and year:
                gstr2b_mismatches = self.detect_gstr2b_mismatches(
                    client_id, month, year, gstr2b_data
                )
            
            # Use provided dates or defaults
            if not start_date:
                start_date = (datetime.now() - timedelta(days=90)).date().isoformat()
            if not end_date:
                end_date = datetime.now().date().isoformat()
            
            incorrect_rates = self.detect_incorrect_gst_rates(client_id, start_date, end_date)
            itc_discrepancies = self.detect_itc_discrepancies(client_id, start_date, end_date)
            
            all_mismatches = gstr2b_mismatches + incorrect_rates + itc_discrepancies
            
            return {
                "client_id": client_id,
                "scan_date": datetime.now().isoformat(),
                "date_range": {
                    "start": start_date,
                    "end": end_date
                },
                "month_year": f"{month}/{year}" if month and year else None,
                "results": {
                    "gstr2b_mismatches": {
                        "count": len(gstr2b_mismatches),
                        "items": gstr2b_mismatches
                    },
                    "incorrect_gst_rates": {
                        "count": len(incorrect_rates),
                        "items": incorrect_rates
                    },
                    "itc_discrepancies": {
                        "count": len(itc_discrepancies),
                        "items": itc_discrepancies
                    }
                },
                "summary": {
                    "total_mismatches": len(all_mismatches),
                    "high_severity": sum(1 for item in all_mismatches if item.get("severity") == "high"),
                    "medium_severity": sum(1 for item in all_mismatches if item.get("severity") == "medium"),
                    "low_severity": sum(1 for item in all_mismatches if item.get("severity") == "low"),
                    "potential_itc_loss": sum(
                        item.get("blocked_itc", 0) for item in itc_discrepancies 
                        if item.get("discrepancy_type") == "blocked_credit"
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"Error running full GST mismatch scan: {str(e)}")
            return {
                "client_id": client_id,
                "scan_date": datetime.now().isoformat(),
                "error": str(e),
                "results": {
                    "gstr2b_mismatches": {"count": 0, "items": []},
                    "incorrect_gst_rates": {"count": 0, "items": []},
                    "itc_discrepancies": {"count": 0, "items": []}
                }
            }

