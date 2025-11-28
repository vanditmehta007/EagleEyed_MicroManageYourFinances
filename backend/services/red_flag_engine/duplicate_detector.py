from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger


class DuplicateDetector:
    """
    Service for detecting duplicate invoices, repeated transactions, and duplicate vendor bills.
    
    Detects:
    - Duplicate invoices (same invoice number and vendor)
    - Repeated transactions (same amount, vendor, and date)
    - Duplicate vendor bills (similar amounts, same vendor, within time window)
    - Near-duplicates using fuzzy matching
    """

    def __init__(self):
        self.amount_tolerance = 0.01  # 1% tolerance for amount matching
        self.date_window_days = 7  # Days within which to consider duplicates
        self.fuzzy_threshold = 0.85  # Similarity threshold for invoice number matching

    def detect_duplicate_invoices(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect duplicate invoices based on invoice number and vendor.
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD). If not provided, checks last 90 days.
            end_date: Optional end date (YYYY-MM-DD). If not provided, uses today.
            
        Returns:
            List of dictionaries containing duplicate invoice groups.
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
            
            # Group by invoice number and vendor
            invoice_groups = defaultdict(list)
            for txn in transactions:
                invoice_number = txn.get("invoice_number", "").strip().upper()
                vendor = txn.get("vendor", "").strip() if txn.get("vendor") else "Unknown"
                key = f"{invoice_number}_{vendor}"
                
                if invoice_number:  # Only process if invoice number exists
                    invoice_groups[key].append(txn)
            
            duplicates = []
            
            # Find groups with multiple transactions (duplicates)
            for key, txns in invoice_groups.items():
                if len(txns) > 1:
                    invoice_number, vendor = key.rsplit("_", 1)
                    total_amount = sum(float(t.get("amount", 0)) for t in txns)
                    
                    # Determine severity based on count and amount
                    if len(txns) > 2:
                        severity = "high"
                    elif total_amount > 100000:
                        severity = "high"
                    else:
                        severity = "medium"
                    
                    duplicates.append({
                        "duplicate_type": "invoice_number",
                        "invoice_number": invoice_number,
                        "vendor": vendor,
                        "duplicate_count": len(txns),
                        "total_amount": total_amount,
                        "transactions": [
                            {
                                "transaction_id": t.get("id"),
                                "date": t.get("date"),
                                "amount": float(t.get("amount", 0)),
                                "description": t.get("description"),
                                "gstin": t.get("gstin")
                            }
                            for t in txns
                        ],
                        "severity": severity,
                        "message": f"Duplicate invoice detected: Invoice '{invoice_number}' from vendor "
                                  f"'{vendor}' appears {len(txns)} times with total amount ₹{total_amount:,.2f}",
                        "recommendation": "Review transactions to identify if this is a legitimate duplicate "
                                        "payment or an error. Duplicate payments may need to be reversed."
                    })
            
            logger.info(f"Detected {len(duplicates)} duplicate invoice groups for client {client_id}")
            return duplicates
            
        except Exception as e:
            logger.error(f"Error detecting duplicate invoices: {str(e)}")
            return []

    def detect_repeated_transactions(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect repeated transactions (same amount, vendor, and date).
        
        This catches cases where the same transaction might have been entered multiple times
        by mistake, even without invoice numbers.
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            List of dictionaries containing repeated transaction groups.
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().date().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=90)).date().isoformat()
            
            # Fetch all transactions
            response = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).gte("date", start_date).lte("date", end_date).is_(
                "deleted_at", "null"
            ).execute()
            
            transactions = response.data if response.data else []
            
            # Group by amount, vendor, and date (exact match)
            transaction_groups = defaultdict(list)
            for txn in transactions:
                amount = round(float(txn.get("amount", 0)), 2)  # Round to 2 decimals
                vendor = txn.get("vendor", "").strip() if txn.get("vendor") else "Unknown"
                date = txn.get("date")
                key = f"{amount}_{vendor}_{date}"
                
                transaction_groups[key].append(txn)
            
            repeated = []
            
            # Find groups with multiple transactions
            for key, txns in transaction_groups.items():
                if len(txns) > 1:
                    amount, vendor, date = key.rsplit("_", 2)
                    total_amount = float(amount) * len(txns)
                    
                    # Determine severity
                    if len(txns) > 2:
                        severity = "high"
                    elif total_amount > 50000:
                        severity = "high"
                    else:
                        severity = "medium"
                    
                    repeated.append({
                        "duplicate_type": "repeated_transaction",
                        "date": date,
                        "vendor": vendor,
                        "amount": float(amount),
                        "duplicate_count": len(txns),
                        "total_amount": total_amount,
                        "transactions": [
                            {
                                "transaction_id": t.get("id"),
                                "invoice_number": t.get("invoice_number"),
                                "description": t.get("description"),
                                "gstin": t.get("gstin"),
                                "mode": t.get("mode")
                            }
                            for t in txns
                        ],
                        "severity": severity,
                        "message": f"Repeated transaction detected: {len(txns)} identical transactions of "
                                  f"₹{amount} to vendor '{vendor}' on {date}. Total: ₹{total_amount:,.2f}",
                        "recommendation": "These transactions appear to be exact duplicates. Verify if this "
                                        "is intentional or if one should be deleted/reversed."
                    })
            
            logger.info(f"Detected {len(repeated)} repeated transaction groups for client {client_id}")
            return repeated
            
        except Exception as e:
            logger.error(f"Error detecting repeated transactions: {str(e)}")
            return []

    def detect_duplicate_vendor_bills(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect duplicate vendor bills (similar amounts, same vendor, within time window).
        
        This catches cases where the same bill might have been paid multiple times
        with slight variations in amount or date.
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            List of dictionaries containing duplicate vendor bill groups.
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().date().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=90)).date().isoformat()
            
            # Fetch all transactions
            response = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).eq("type", "debit").gte("date", start_date).lte("date", end_date).is_(
                "deleted_at", "null"
            ).execute()
            
            transactions = response.data if response.data else []
            
            # Group by vendor
            vendor_transactions = defaultdict(list)
            for txn in transactions:
                vendor = txn.get("vendor", "").strip() if txn.get("vendor") else "Unknown"
                if vendor and vendor != "Unknown":
                    vendor_transactions[vendor].append(txn)
            
            duplicates = []
            
            # For each vendor, find similar transactions within date window
            for vendor, txns in vendor_transactions.items():
                if len(txns) < 2:
                    continue
                
                # Sort by date
                txns_sorted = sorted(txns, key=lambda x: x.get("date", ""))
                
                # Check for similar amounts within date window
                i = 0
                while i < len(txns_sorted):
                    current_txn = txns_sorted[i]
                    current_amount = float(current_txn.get("amount", 0))
                    current_date = datetime.fromisoformat(current_txn.get("date"))
                    
                    similar_group = [current_txn]
                    
                    # Look for similar transactions within date window
                    j = i + 1
                    while j < len(txns_sorted):
                        next_txn = txns_sorted[j]
                        next_amount = float(next_txn.get("amount", 0))
                        next_date = datetime.fromisoformat(next_txn.get("date"))
                        
                        # Check if within date window
                        days_diff = (next_date - current_date).days
                        if days_diff > self.date_window_days:
                            break
                        
                        # Check if amounts are similar (within tolerance)
                        amount_diff = abs(current_amount - next_amount)
                        amount_tolerance_value = current_amount * self.amount_tolerance
                        
                        if amount_diff <= amount_tolerance_value or amount_diff <= 100:  # ₹100 absolute tolerance
                            similar_group.append(next_txn)
                        
                        j += 1
                    
                    # If we found similar transactions, add to duplicates
                    if len(similar_group) > 1:
                        total_amount = sum(float(t.get("amount", 0)) for t in similar_group)
                        avg_amount = total_amount / len(similar_group)
                        
                        # Determine severity
                        if len(similar_group) > 2:
                            severity = "high"
                        elif total_amount > 100000:
                            severity = "high"
                        else:
                            severity = "medium"
                        
                        duplicates.append({
                            "duplicate_type": "vendor_bill",
                            "vendor": vendor,
                            "duplicate_count": len(similar_group),
                            "average_amount": round(avg_amount, 2),
                            "total_amount": round(total_amount, 2),
                            "date_range": {
                                "start": min(t.get("date") for t in similar_group),
                                "end": max(t.get("date") for t in similar_group)
                            },
                            "transactions": [
                                {
                                    "transaction_id": t.get("id"),
                                    "date": t.get("date"),
                                    "amount": float(t.get("amount", 0)),
                                    "invoice_number": t.get("invoice_number"),
                                    "description": t.get("description"),
                                    "gstin": t.get("gstin")
                                }
                                for t in similar_group
                            ],
                            "severity": severity,
                            "message": f"Duplicate vendor bill detected: {len(similar_group)} similar transactions "
                                      f"to vendor '{vendor}' with average amount ₹{avg_amount:,.2f} "
                                      f"(total: ₹{total_amount:,.2f}) within {self.date_window_days} days",
                            "recommendation": "These transactions appear to be duplicate payments for the same "
                                            "vendor bill. Verify if multiple payments were intentional or if "
                                            "one should be reversed."
                        })
                        
                        # Skip transactions we've already grouped
                        i = j
                    else:
                        i += 1
            
            logger.info(f"Detected {len(duplicates)} duplicate vendor bill groups for client {client_id}")
            return duplicates
            
        except Exception as e:
            logger.error(f"Error detecting duplicate vendor bills: {str(e)}")
            return []

    def detect_near_duplicate_invoices(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect near-duplicate invoices using fuzzy matching on invoice numbers.
        
        This catches cases where invoice numbers are similar but not exactly the same
        (e.g., "INV-001" vs "INV-001A" or typos).
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            List of dictionaries containing near-duplicate invoice groups.
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
            
            # Simple fuzzy matching using string similarity
            def similarity(s1: str, s2: str) -> float:
                """Calculate simple similarity ratio between two strings."""
                s1 = s1.upper().strip()
                s2 = s2.upper().strip()
                
                if s1 == s2:
                    return 1.0
                
                # Check if one contains the other
                if s1 in s2 or s2 in s1:
                    return 0.9
                
                # Calculate character overlap
                common_chars = sum(1 for c in s1 if c in s2)
                max_len = max(len(s1), len(s2))
                if max_len == 0:
                    return 0.0
                
                return common_chars / max_len
            
            # Group by vendor first, then find similar invoice numbers
            vendor_invoices = defaultdict(list)
            for txn in transactions:
                vendor = txn.get("vendor", "").strip() if txn.get("vendor") else "Unknown"
                if vendor and vendor != "Unknown":
                    vendor_invoices[vendor].append(txn)
            
            near_duplicates = []
            
            # For each vendor, find similar invoice numbers
            for vendor, txns in vendor_invoices.items():
                if len(txns) < 2:
                    continue
                
                # Compare all pairs
                processed = set()
                for i, txn1 in enumerate(txns):
                    if i in processed:
                        continue
                    
                    inv1 = txn1.get("invoice_number", "").strip().upper()
                    if not inv1:
                        continue
                    
                    similar_group = [txn1]
                    
                    for j, txn2 in enumerate(txns[i+1:], start=i+1):
                        if j in processed:
                            continue
                        
                        inv2 = txn2.get("invoice_number", "").strip().upper()
                        if not inv2:
                            continue
                        
                        sim = similarity(inv1, inv2)
                        if sim >= self.fuzzy_threshold:
                            similar_group.append(txn2)
                            processed.add(j)
                    
                    if len(similar_group) > 1:
                        processed.add(i)
                        
                        total_amount = sum(float(t.get("amount", 0)) for t in similar_group)
                        invoice_numbers = [t.get("invoice_number", "").strip() for t in similar_group]
                        
                        near_duplicates.append({
                            "duplicate_type": "near_duplicate_invoice",
                            "vendor": vendor,
                            "invoice_numbers": invoice_numbers,
                            "duplicate_count": len(similar_group),
                            "total_amount": round(total_amount, 2),
                            "transactions": [
                                {
                                    "transaction_id": t.get("id"),
                                    "date": t.get("date"),
                                    "amount": float(t.get("amount", 0)),
                                    "invoice_number": t.get("invoice_number"),
                                    "description": t.get("description")
                                }
                                for t in similar_group
                            ],
                            "severity": "low",
                            "message": f"Near-duplicate invoices detected: Similar invoice numbers "
                                      f"({', '.join(invoice_numbers)}) from vendor '{vendor}' with "
                                      f"total amount ₹{total_amount:,.2f}",
                            "recommendation": "These invoice numbers are similar but not identical. "
                                            "Verify if they represent the same invoice or different invoices."
                        })
            
            logger.info(f"Detected {len(near_duplicates)} near-duplicate invoice groups for client {client_id}")
            return near_duplicates
            
        except Exception as e:
            logger.error(f"Error detecting near-duplicate invoices: {str(e)}")
            return []

    def run_full_scan(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a comprehensive duplicate detection scan combining all methods.
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            Dictionary containing all detected duplicates categorized by type.
        """
        try:
            duplicate_invoices = self.detect_duplicate_invoices(client_id, start_date, end_date)
            repeated_transactions = self.detect_repeated_transactions(client_id, start_date, end_date)
            duplicate_bills = self.detect_duplicate_vendor_bills(client_id, start_date, end_date)
            near_duplicates = self.detect_near_duplicate_invoices(client_id, start_date, end_date)
            
            all_duplicates = duplicate_invoices + repeated_transactions + duplicate_bills + near_duplicates
            
            return {
                "client_id": client_id,
                "scan_date": datetime.now().isoformat(),
                "date_range": {
                    "start": start_date or (datetime.now() - timedelta(days=90)).date().isoformat(),
                    "end": end_date or datetime.now().date().isoformat()
                },
                "results": {
                    "duplicate_invoices": {
                        "count": len(duplicate_invoices),
                        "items": duplicate_invoices
                    },
                    "repeated_transactions": {
                        "count": len(repeated_transactions),
                        "items": repeated_transactions
                    },
                    "duplicate_vendor_bills": {
                        "count": len(duplicate_bills),
                        "items": duplicate_bills
                    },
                    "near_duplicate_invoices": {
                        "count": len(near_duplicates),
                        "items": near_duplicates
                    }
                },
                "summary": {
                    "total_duplicates": len(all_duplicates),
                    "high_severity": sum(1 for item in all_duplicates if item.get("severity") == "high"),
                    "medium_severity": sum(1 for item in all_duplicates if item.get("severity") == "medium"),
                    "low_severity": sum(1 for item in all_duplicates if item.get("severity") == "low"),
                    "total_potential_loss": sum(item.get("total_amount", 0) for item in all_duplicates)
                }
            }
            
        except Exception as e:
            logger.error(f"Error running full duplicate detection scan: {str(e)}")
            return {
                "client_id": client_id,
                "scan_date": datetime.now().isoformat(),
                "error": str(e),
                "results": {
                    "duplicate_invoices": {"count": 0, "items": []},
                    "repeated_transactions": {"count": 0, "items": []},
                    "duplicate_vendor_bills": {"count": 0, "items": []},
                    "near_duplicate_invoices": {"count": 0, "items": []}
                }
            }

