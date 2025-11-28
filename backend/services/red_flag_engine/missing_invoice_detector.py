from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from backend.utils.supabase_client import supabase
from backend.config import settings
from backend.utils.logger import logger


class MissingInvoiceDetector:
    """
    Service for detecting expenses or credits without corresponding invoice documents.
    
    Detects:
    - Transactions without invoice numbers
    - Transactions with invoice numbers but no corresponding document
    - Large transactions that should have invoices
    - GST-applicable transactions without invoices
    - Vendor transactions without supporting documents
    """

    def __init__(self):
        self.invoice_required_threshold = 5000.0  # Transactions above this should have invoices
        self.large_transaction_threshold = 10000.0  # Large transactions definitely need invoices
        self.gst_threshold = 0.0  # All GST-applicable transactions need invoices

    def detect_missing_invoice_numbers(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect transactions without invoice numbers.
        
        Flags:
        - Debit transactions (expenses) without invoice numbers
        - Credit transactions (income) without invoice numbers
        - Large transactions that should have invoice numbers
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD). If not provided, checks last 90 days.
            end_date: Optional end date (YYYY-MM-DD). If not provided, uses today.
            
        Returns:
            List of dictionaries containing transactions missing invoice numbers.
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().date().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=90)).date().isoformat()
            
            # Fetch transactions without invoice numbers
            response = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).is_("invoice_number", "null").gte("date", start_date).lte(
                "date", end_date
            ).is_("deleted_at", "null").execute()
            
            transactions = response.data if response.data else []
            missing_invoices = []
            
            for txn in transactions:
                amount = float(txn.get("amount", 0))
                txn_type = txn.get("type")
                vendor = txn.get("vendor")
                gst_applicable = txn.get("gst_applicable", False)
                
                # Determine severity based on amount and type
                if amount >= self.large_transaction_threshold:
                    severity = "high"
                    reason = f"Large transaction of ₹{amount:,.2f} requires invoice"
                elif amount >= self.invoice_required_threshold:
                    severity = "medium"
                    reason = f"Transaction of ₹{amount:,.2f} should have invoice"
                elif gst_applicable:
                    severity = "high"
                    reason = "GST-applicable transaction requires invoice for ITC claim"
                else:
                    severity = "low"
                    reason = "Transaction missing invoice number"
                
                missing_invoices.append({
                    "issue_type": "missing_invoice_number",
                    "transaction_id": txn.get("id"),
                    "date": txn.get("date"),
                    "type": txn_type,
                    "amount": amount,
                    "vendor": vendor,
                    "description": txn.get("description"),
                    "gst_applicable": gst_applicable,
                    "gstin": txn.get("gstin"),
                    "severity": severity,
                    "message": f"{reason}. Transaction: {txn.get('description')} "
                              f"to vendor '{vendor}' on {txn.get('date')}",
                    "implication": "Missing invoice number may cause compliance issues. "
                                 "For GST transactions, ITC cannot be claimed without proper invoice. "
                                 "For large transactions, invoice is required for audit purposes.",
                    "law_reference": "CGST Act, 2017 - Section 16(2) for GST transactions, "
                                   "Income Tax Act - Section 40A(3) for large transactions"
                })
            
            logger.info(f"Detected {len(missing_invoices)} transactions missing invoice numbers for client {client_id}")
            return missing_invoices
            
        except Exception as e:
            logger.error(f"Error detecting missing invoice numbers: {str(e)}")
            return []

    def detect_missing_invoice_documents(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect transactions with invoice numbers but no corresponding document.
        
        Checks if invoice documents exist in the documents table by matching invoice numbers
        from transaction metadata with document metadata.
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            List of dictionaries containing transactions with missing invoice documents.
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().date().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=90)).date().isoformat()
            
            # Fetch transactions with invoice numbers
            response = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).not_.is_("invoice_number", "null").gte("date", start_date).lte(
                "date", end_date
            ).is_("deleted_at", "null").execute()
            
            transactions = response.data if response.data else []
            
            # Fetch all documents for the client
            doc_response = supabase.table("documents").select("*").eq(
                "client_id", client_id
            ).is_("deleted_at", "null").execute()
            
            documents = doc_response.data if doc_response.data else []
            
            # Create set of invoice numbers from documents metadata
            document_invoice_numbers = set()
            for doc in documents:
                metadata = doc.get("metadata", {})
                if isinstance(metadata, dict):
                    invoice_no = metadata.get("invoice_number") or metadata.get("invoice_no")
                    if invoice_no:
                        document_invoice_numbers.add(str(invoice_no).strip().upper())
            
            missing_documents = []
            
            for txn in transactions:
                invoice_number = txn.get("invoice_number", "").strip().upper()
                if not invoice_number:
                    continue
                
                # Check if invoice number exists in documents
                if invoice_number not in document_invoice_numbers:
                    amount = float(txn.get("amount", 0))
                    txn_type = txn.get("type")
                    vendor = txn.get("vendor")
                    gst_applicable = txn.get("gst_applicable", False)
                    
                    # Determine severity
                    if gst_applicable:
                        severity = "high"
                        reason = "GST transaction requires invoice document for ITC claim"
                    elif amount >= self.large_transaction_threshold:
                        severity = "high"
                        reason = "Large transaction requires invoice document for audit"
                    else:
                        severity = "medium"
                        reason = "Transaction has invoice number but document not found"
                    
                    missing_documents.append({
                        "issue_type": "missing_invoice_document",
                        "transaction_id": txn.get("id"),
                        "invoice_number": invoice_number,
                        "date": txn.get("date"),
                        "type": txn_type,
                        "amount": amount,
                        "vendor": vendor,
                        "description": txn.get("description"),
                        "gst_applicable": gst_applicable,
                        "gstin": txn.get("gstin"),
                        "severity": severity,
                        "message": f"{reason}. Invoice number: {invoice_number}, "
                                  f"Vendor: {vendor}, Amount: ₹{amount:,.2f}",
                        "implication": "Invoice document is required for compliance and audit purposes. "
                                     "Without the physical document, ITC claims may be disallowed. "
                                     "Please upload the invoice document.",
                        "law_reference": "CGST Act, 2017 - Section 16(2) requires invoice document for ITC"
                    })
            
            logger.info(f"Detected {len(missing_documents)} transactions with missing invoice documents for client {client_id}")
            return missing_documents
            
        except Exception as e:
            logger.error(f"Error detecting missing invoice documents: {str(e)}")
            return []

    def detect_gst_transactions_without_invoices(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Specifically detect GST-applicable transactions without invoices.
        
        These are critical as ITC cannot be claimed without proper invoices.
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            List of dictionaries containing GST transactions without invoices.
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().date().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=90)).date().isoformat()
            
            # Fetch GST-applicable debit transactions (purchases) without invoice numbers
            response = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).eq("type", "debit").eq("gst_applicable", True).is_(
                "invoice_number", "null"
            ).gte("date", start_date).lte("date", end_date).is_(
                "deleted_at", "null"
            ).execute()
            
            transactions = response.data if response.data else []
            gst_issues = []
            
            for txn in transactions:
                amount = float(txn.get("amount", 0))
                vendor = txn.get("vendor")
                gstin = txn.get("gstin")
                
                # Calculate potential ITC loss
                gst_rate = settings.GST_RATE_DEFAULT
                taxable_value = amount / (1 + gst_rate / 100)
                itc_amount = amount - taxable_value
                
                gst_issues.append({
                    "issue_type": "gst_without_invoice",
                    "transaction_id": txn.get("id"),
                    "date": txn.get("date"),
                    "amount": amount,
                    "vendor": vendor,
                    "gstin": gstin,
                    "description": txn.get("description"),
                    "potential_itc_loss": round(itc_amount, 2),
                    "severity": "high",
                    "message": f"GST transaction without invoice: ₹{amount:,.2f} to vendor '{vendor}'. "
                              f"Potential ITC loss: ₹{itc_amount:,.2f}",
                    "implication": f"ITC of ₹{itc_amount:,.2f} cannot be claimed without proper invoice. "
                                 "This will increase tax liability. Invoice is mandatory for GST transactions.",
                    "law_reference": "CGST Act, 2017 - Section 16(2) - ITC can only be claimed with valid invoice"
                })
            
            logger.info(f"Detected {len(gst_issues)} GST transactions without invoices for client {client_id}")
            return gst_issues
            
        except Exception as e:
            logger.error(f"Error detecting GST transactions without invoices: {str(e)}")
            return []

    def detect_vendor_transactions_without_documents(
        self, 
        client_id: str, 
        vendor: Optional[str] = None,
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect vendor transactions without supporting documents.
        
        Useful for identifying vendors that consistently don't provide invoices
        or for auditing specific vendor relationships.
        
        Args:
            client_id: Client identifier.
            vendor: Optional vendor name to filter by.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            List of dictionaries containing vendor transactions without documents.
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().date().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=90)).date().isoformat()
            
            # Build query
            query = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).eq("type", "debit").gte("date", start_date).lte(
                "date", end_date
            ).is_("deleted_at", "null")
            
            if vendor:
                query = query.eq("vendor", vendor)
            
            response = query.execute()
            transactions = response.data if response.data else []
            
            # Fetch documents
            doc_response = supabase.table("documents").select("*").eq(
                "client_id", client_id
            ).is_("deleted_at", "null").execute()
            
            documents = doc_response.data if doc_response.data else []
            
            # Create lookup of invoice numbers from documents
            document_invoice_numbers = set()
            for doc in documents:
                metadata = doc.get("metadata", {})
                if isinstance(metadata, dict):
                    invoice_no = metadata.get("invoice_number") or metadata.get("invoice_no")
                    if invoice_no:
                        document_invoice_numbers.add(str(invoice_no).strip().upper())
            
            # Group transactions by vendor
            vendor_transactions = {}
            for txn in transactions:
                vendor_name = txn.get("vendor", "Unknown")
                if vendor_name not in vendor_transactions:
                    vendor_transactions[vendor_name] = []
                vendor_transactions[vendor_name].append(txn)
            
            vendor_issues = []
            
            for vendor_name, txns in vendor_transactions.items():
                missing_count = 0
                total_amount = 0.0
                missing_txns = []
                
                for txn in txns:
                    invoice_number = txn.get("invoice_number", "").strip().upper()
                    amount = float(txn.get("amount", 0))
                    
                    # Check if missing invoice number or document
                    if not invoice_number or invoice_number not in document_invoice_numbers:
                        missing_count += 1
                        total_amount += amount
                        missing_txns.append({
                            "transaction_id": txn.get("id"),
                            "date": txn.get("date"),
                            "amount": amount,
                            "invoice_number": invoice_number or "Missing",
                            "description": txn.get("description")
                        })
                
                if missing_count > 0:
                    # Determine severity based on count and amount
                    if missing_count >= 5 or total_amount > 100000:
                        severity = "high"
                    elif missing_count >= 3 or total_amount > 50000:
                        severity = "medium"
                    else:
                        severity = "low"
                    
                    vendor_issues.append({
                        "issue_type": "vendor_missing_documents",
                        "vendor": vendor_name,
                        "total_transactions": len(txns),
                        "missing_document_count": missing_count,
                        "total_amount_missing": round(total_amount, 2),
                        "transactions": missing_txns,
                        "severity": severity,
                        "message": f"Vendor '{vendor_name}' has {missing_count} transactions "
                                  f"({len(txns)} total) without proper invoice documents. "
                                  f"Total amount: ₹{total_amount:,.2f}",
                        "implication": f"Multiple transactions with vendor '{vendor_name}' are missing "
                                     "invoice documents. This may indicate a pattern of non-compliance. "
                                     "Request invoices from vendor for all transactions.",
                        "recommendation": "Contact vendor to obtain missing invoices. Consider reviewing "
                                        "vendor relationship if pattern persists."
                    })
            
            logger.info(f"Detected {len(vendor_issues)} vendors with missing documents for client {client_id}")
            return vendor_issues
            
        except Exception as e:
            logger.error(f"Error detecting vendor transactions without documents: {str(e)}")
            return []

    def run_full_scan(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a comprehensive missing invoice detection scan combining all methods.
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            Dictionary containing all detected missing invoice issues categorized by type.
        """
        try:
            missing_numbers = self.detect_missing_invoice_numbers(client_id, start_date, end_date)
            missing_documents = self.detect_missing_invoice_documents(client_id, start_date, end_date)
            gst_issues = self.detect_gst_transactions_without_invoices(client_id, start_date, end_date)
            vendor_issues = self.detect_vendor_transactions_without_documents(client_id, None, start_date, end_date)
            
            all_issues = missing_numbers + missing_documents + gst_issues
            
            # Calculate total potential ITC loss
            total_itc_loss = sum(
                issue.get("potential_itc_loss", 0) for issue in gst_issues
            )
            
            return {
                "client_id": client_id,
                "scan_date": datetime.now().isoformat(),
                "date_range": {
                    "start": start_date or (datetime.now() - timedelta(days=90)).date().isoformat(),
                    "end": end_date or datetime.now().date().isoformat()
                },
                "results": {
                    "missing_invoice_numbers": {
                        "count": len(missing_numbers),
                        "items": missing_numbers
                    },
                    "missing_invoice_documents": {
                        "count": len(missing_documents),
                        "items": missing_documents
                    },
                    "gst_transactions_without_invoices": {
                        "count": len(gst_issues),
                        "items": gst_issues
                    },
                    "vendor_missing_documents": {
                        "count": len(vendor_issues),
                        "items": vendor_issues
                    }
                },
                "summary": {
                    "total_issues": len(all_issues) + len(vendor_issues),
                    "high_severity": sum(1 for item in all_issues if item.get("severity") == "high"),
                    "medium_severity": sum(1 for item in all_issues if item.get("severity") == "medium"),
                    "low_severity": sum(1 for item in all_issues if item.get("severity") == "low"),
                    "total_potential_itc_loss": round(total_itc_loss, 2),
                    "vendors_with_issues": len(vendor_issues)
                }
            }
            
        except Exception as e:
            logger.error(f"Error running full missing invoice scan: {str(e)}")
            return {
                "client_id": client_id,
                "scan_date": datetime.now().isoformat(),
                "error": str(e),
                "results": {
                    "missing_invoice_numbers": {"count": 0, "items": []},
                    "missing_invoice_documents": {"count": 0, "items": []},
                    "gst_transactions_without_invoices": {"count": 0, "items": []},
                    "vendor_missing_documents": {"count": 0, "items": []}
                }
            }

