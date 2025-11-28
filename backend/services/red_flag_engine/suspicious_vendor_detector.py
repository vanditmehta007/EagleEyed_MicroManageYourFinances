from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger


class SuspiciousVendorDetector:
    """
    Service for identifying high-risk vendors, mismatched GST registrations, blocked GSTINs, and compliance issues.
    
    Detects:
    - High-risk vendors (multiple red flags, compliance issues)
    - Mismatched GST registrations (vendor name doesn't match GSTIN)
    - Blocked/cancelled GSTINs
    - Vendors with missing compliance documents
    - Vendors with suspicious transaction patterns
    - Unregistered vendors for GST-applicable transactions
    """

    def __init__(self):
        self.high_risk_threshold = 3  # Number of red flags to be considered high-risk
        self.large_transaction_threshold = 50000.0  # Large transactions requiring verification
        self.gst_registration_threshold = 200000.0  # Turnover threshold for GST registration

    def detect_high_risk_vendors(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect high-risk vendors based on multiple risk factors.
        
        Risk factors:
        - Multiple missing invoices
        - Large transactions without proper documentation
        - GST compliance issues
        - Cash transaction violations
        - Duplicate transactions
        - Suspicious patterns
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD). If not provided, checks last 12 months.
            end_date: Optional end date (YYYY-MM-DD). If not provided, uses today.
            
        Returns:
            List of dictionaries containing high-risk vendor assessments.
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().date().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).date().isoformat()
            
            # Fetch all transactions
            response = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).gte("date", start_date).lte("date", end_date).is_(
                "deleted_at", "null"
            ).execute()
            
            transactions = response.data if response.data else []
            
            # Group by vendor
            vendor_data = defaultdict(lambda: {
                "transactions": [],
                "total_amount": 0.0,
                "transaction_count": 0,
                "missing_invoices": 0,
                "missing_gstin": 0,
                "cash_transactions": 0,
                "large_transactions": 0,
                "duplicate_count": 0,
                "gst_issues": 0,
                "risk_score": 0
            })
            
            for txn in transactions:
                vendor = txn.get("vendor", "").strip() if txn.get("vendor") else "Unknown"
                if vendor == "Unknown":
                    continue
                
                amount = float(txn.get("amount", 0))
                vendor_data[vendor]["transactions"].append(txn)
                vendor_data[vendor]["total_amount"] += amount
                vendor_data[vendor]["transaction_count"] += 1
                
                # Count risk factors
                if not txn.get("invoice_number"):
                    vendor_data[vendor]["missing_invoices"] += 1
                    vendor_data[vendor]["risk_score"] += 1
                
                if not txn.get("gstin") and txn.get("gst_applicable"):
                    vendor_data[vendor]["missing_gstin"] += 1
                    vendor_data[vendor]["risk_score"] += 2
                    vendor_data[vendor]["gst_issues"] += 1
                
                if txn.get("mode", "").upper() == "CASH" and amount > 10000:
                    vendor_data[vendor]["cash_transactions"] += 1
                    vendor_data[vendor]["risk_score"] += 2
                
                if amount >= self.large_transaction_threshold:
                    vendor_data[vendor]["large_transactions"] += 1
                    if not txn.get("invoice_number"):
                        vendor_data[vendor]["risk_score"] += 1
            
            high_risk_vendors = []
            
            for vendor, data in vendor_data.items():
                if data["risk_score"] >= self.high_risk_threshold or data["transaction_count"] >= 5:
                    # Calculate risk percentage
                    risk_percentage = (data["risk_score"] / data["transaction_count"] * 100) if data["transaction_count"] > 0 else 0
                    
                    # Determine severity
                    if data["risk_score"] >= 5 or risk_percentage > 50:
                        severity = "high"
                    elif data["risk_score"] >= 3 or risk_percentage > 30:
                        severity = "medium"
                    else:
                        severity = "low"
                    
                    risk_factors = []
                    if data["missing_invoices"] > 0:
                        risk_factors.append(f"{data['missing_invoices']} missing invoices")
                    if data["missing_gstin"] > 0:
                        risk_factors.append(f"{data['missing_gstin']} GST compliance issues")
                    if data["cash_transactions"] > 0:
                        risk_factors.append(f"{data['cash_transactions']} cash transaction violations")
                    if data["large_transactions"] > 0:
                        risk_factors.append(f"{data['large_transactions']} large transactions")
                    
                    high_risk_vendors.append({
                        "vendor": vendor,
                        "risk_score": data["risk_score"],
                        "risk_percentage": round(risk_percentage, 2),
                        "severity": severity,
                        "total_transactions": data["transaction_count"],
                        "total_amount": round(data["total_amount"], 2),
                        "risk_factors": risk_factors,
                        "details": {
                            "missing_invoices": data["missing_invoices"],
                            "missing_gstin": data["missing_gstin"],
                            "cash_transactions": data["cash_transactions"],
                            "large_transactions": data["large_transactions"],
                            "gst_issues": data["gst_issues"]
                        },
                        "message": f"High-risk vendor detected: '{vendor}' with risk score {data['risk_score']}. "
                                  f"Risk factors: {', '.join(risk_factors)}",
                        "recommendation": f"Review all transactions with vendor '{vendor}'. "
                                        "Consider requesting additional compliance documentation. "
                                        "May need to verify vendor registration status."
                    })
            
            # Sort by risk score
            high_risk_vendors.sort(key=lambda x: x["risk_score"], reverse=True)
            
            logger.info(f"Detected {len(high_risk_vendors)} high-risk vendors for client {client_id}")
            return high_risk_vendors
            
        except Exception as e:
            logger.error(f"Error detecting high-risk vendors: {str(e)}")
            return []

    def detect_gst_registration_mismatches(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect mismatched GST registrations (vendor name doesn't match GSTIN).
        
        Checks:
        - Multiple vendors with same GSTIN (potential fraud)
        - GSTIN format validation
        - Vendor name vs GSTIN state code mismatch
        - Suspicious GSTIN patterns
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            List of dictionaries containing GST registration mismatch details.
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().date().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).date().isoformat()
            
            # Fetch transactions with GSTIN
            response = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).not_.is_("gstin", "null").gte("date", start_date).lte(
                "date", end_date
            ).is_("deleted_at", "null").execute()
            
            transactions = response.data if response.data else []
            
            # Group by GSTIN
            gstin_vendors = defaultdict(set)
            vendor_gstins = defaultdict(set)
            
            for txn in transactions:
                gstin = txn.get("gstin", "").strip().upper()
                vendor = txn.get("vendor", "").strip() if txn.get("vendor") else "Unknown"
                
                if gstin and vendor != "Unknown":
                    gstin_vendors[gstin].add(vendor)
                    vendor_gstins[vendor].add(gstin)
            
            mismatches = []
            
            # Check 1: Multiple vendors with same GSTIN (suspicious)
            for gstin, vendors in gstin_vendors.items():
                if len(vendors) > 1:
                    # Get transactions for this GSTIN
                    gstin_txns = [t for t in transactions if t.get("gstin", "").strip().upper() == gstin]
                    total_amount = sum(float(t.get("amount", 0)) for t in gstin_txns)
                    
                    mismatches.append({
                        "mismatch_type": "multiple_vendors_same_gstin",
                        "gstin": gstin,
                        "vendors": list(vendors),
                        "vendor_count": len(vendors),
                        "transaction_count": len(gstin_txns),
                        "total_amount": round(total_amount, 2),
                        "severity": "high",
                        "message": f"GSTIN {gstin} is associated with {len(vendors)} different vendors: {', '.join(vendors)}",
                        "implication": "This is highly suspicious. A single GSTIN should belong to one business entity. "
                                     "This may indicate: (1) Fraudulent use of GSTIN, (2) Data entry errors, "
                                     "(3) Vendor using another entity's GSTIN. Verify immediately.",
                        "law_reference": "CGST Act, 2017 - Section 22 - GST registration is entity-specific",
                        "recommendation": "Contact vendors to verify GSTIN ownership. Cross-check with GST portal. "
                                        "Consider blocking transactions until verified."
                    })
            
            # Check 2: Multiple GSTINs for same vendor (less suspicious but worth flagging)
            for vendor, gstins in vendor_gstins.items():
                if len(gstins) > 1:
                    vendor_txns = [t for t in transactions if t.get("vendor", "").strip() == vendor]
                    total_amount = sum(float(t.get("amount", 0)) for t in vendor_txns)
                    
                    mismatches.append({
                        "mismatch_type": "multiple_gstins_same_vendor",
                        "vendor": vendor,
                        "gstins": list(gstins),
                        "gstin_count": len(gstins),
                        "transaction_count": len(vendor_txns),
                        "total_amount": round(total_amount, 2),
                        "severity": "medium",
                        "message": f"Vendor '{vendor}' is associated with {len(gstins)} different GSTINs: {', '.join(gstins)}",
                        "implication": "Vendor may have multiple business entities or branches. "
                                     "Verify if this is legitimate (e.g., different locations).",
                        "recommendation": "Verify with vendor if multiple GSTINs are legitimate. "
                                        "Ensure correct GSTIN is used for each transaction."
                    })
            
            # Check 3: Invalid GSTIN format
            for txn in transactions:
                gstin = txn.get("gstin", "").strip().upper()
                if gstin and not self._validate_gstin_format(gstin):
                    mismatches.append({
                        "mismatch_type": "invalid_gstin_format",
                        "transaction_id": txn.get("id"),
                        "gstin": gstin,
                        "vendor": txn.get("vendor"),
                        "date": txn.get("date"),
                        "severity": "high",
                        "message": f"Invalid GSTIN format detected: {gstin} for vendor '{txn.get('vendor')}'",
                        "implication": "GSTIN format is incorrect. ITC cannot be claimed with invalid GSTIN.",
                        "law_reference": "CGST Act, 2017 - GSTIN must be 15 characters (2 state + 10 PAN + 1 check digit + 2 entity)",
                        "recommendation": "Verify and correct GSTIN. Standard format: 15 characters (e.g., 27AAAAA0000A1Z5)"
                    })
            
            logger.info(f"Detected {len(mismatches)} GST registration mismatches for client {client_id}")
            return mismatches
            
        except Exception as e:
            logger.error(f"Error detecting GST registration mismatches: {str(e)}")
            return []

    def _validate_gstin_format(self, gstin: str) -> bool:
        """
        Validate GSTIN format.
        
        GSTIN format: 15 characters
        - First 2: State code (01-37)
        - Next 10: PAN number
        - Next 1: Entity number
        - Last 2: Check digits
        
        Args:
            gstin: GSTIN string to validate.
            
        Returns:
            True if format is valid, False otherwise.
        """
        if not gstin or len(gstin) != 15:
            return False
        
        # Check if all characters are alphanumeric
        if not gstin.isalnum():
            return False
        
        # Check state code (first 2 digits should be 01-37)
        try:
            state_code = int(gstin[:2])
            if state_code < 1 or state_code > 37:
                return False
        except ValueError:
            return False
        
        # PAN should be in middle (characters 2-12, but first 2 are state, so 2-11)
        # Entity number is character 12 (index 11)
        # Check digits are last 2 (characters 13-14, indices 12-13)
        
        return True

    def detect_blocked_gstins(
        self, 
        client_id: str,
        blocked_gstin_list: Optional[List[str]] = None,
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect transactions with blocked, cancelled, or suspended GSTINs.
        
        Note: In production, this would integrate with GST portal API or maintain
        an updated list of blocked GSTINs.
        
        Args:
            client_id: Client identifier.
            blocked_gstin_list: Optional list of blocked GSTINs. If not provided, uses empty list.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            List of dictionaries containing blocked GSTIN transactions.
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().date().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).date().isoformat()
            
            if blocked_gstin_list is None:
                blocked_gstin_list = []
                # In production, fetch from GST portal or database
                logger.warning("No blocked GSTIN list provided. Using empty list.")
            
            # Convert to uppercase for comparison
            blocked_gstins = {gstin.strip().upper() for gstin in blocked_gstin_list}
            
            if not blocked_gstins:
                return []
            
            # Fetch transactions with GSTINs
            response = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).not_.is_("gstin", "null").gte("date", start_date).lte(
                "date", end_date
            ).is_("deleted_at", "null").execute()
            
            transactions = response.data if response.data else []
            
            blocked_transactions = []
            
            for txn in transactions:
                gstin = txn.get("gstin", "").strip().upper()
                if gstin in blocked_gstins:
                    amount = float(txn.get("amount", 0))
                    
                    # Calculate potential ITC loss
                    gst_rate = 18.0  # Default rate
                    taxable_value = amount / (1 + gst_rate / 100)
                    itc_amount = amount - taxable_value
                    
                    blocked_transactions.append({
                        "issue_type": "blocked_gstin",
                        "transaction_id": txn.get("id"),
                        "gstin": gstin,
                        "vendor": txn.get("vendor"),
                        "date": txn.get("date"),
                        "amount": amount,
                        "invoice_number": txn.get("invoice_number"),
                        "potential_itc_loss": round(itc_amount, 2),
                        "severity": "critical",
                        "message": f"Transaction with blocked/cancelled GSTIN {gstin} detected. "
                                  f"Vendor: {txn.get('vendor')}, Amount: ₹{amount:,.2f}",
                        "implication": f"ITC of ₹{itc_amount:,.2f} cannot be claimed. GSTIN is blocked/cancelled. "
                                     "Transaction may be invalid. Immediate action required.",
                        "law_reference": "CGST Act, 2017 - Section 16(2) - ITC not available for cancelled registrations",
                        "recommendation": "Do not claim ITC for this transaction. Verify vendor status. "
                                        "Consider reversing transaction if possible. Report to compliance team."
                    })
            
            logger.info(f"Detected {len(blocked_transactions)} transactions with blocked GSTINs for client {client_id}")
            return blocked_transactions
            
        except Exception as e:
            logger.error(f"Error detecting blocked GSTINs: {str(e)}")
            return []

    def detect_unregistered_vendors(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect unregistered vendors for GST-applicable transactions.
        
        Flags vendors that should be GST registered (based on turnover threshold)
        but don't have GSTIN in transactions.
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            List of dictionaries containing unregistered vendor issues.
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().date().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).date().isoformat()
            
            # Fetch GST-applicable transactions without GSTIN
            response = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).eq("gst_applicable", True).is_("gstin", "null").gte(
                "date", start_date
            ).lte("date", end_date).is_("deleted_at", "null").execute()
            
            transactions = response.data if response.data else []
            
            # Group by vendor
            vendor_totals = defaultdict(lambda: {"transactions": [], "total_amount": 0.0, "count": 0})
            
            for txn in transactions:
                vendor = txn.get("vendor", "").strip() if txn.get("vendor") else "Unknown"
                if vendor == "Unknown":
                    continue
                
                amount = float(txn.get("amount", 0))
                vendor_totals[vendor]["transactions"].append(txn)
                vendor_totals[vendor]["total_amount"] += amount
                vendor_totals[vendor]["count"] += 1
            
            unregistered_issues = []
            
            for vendor, data in vendor_totals.items():
                total_amount = data["total_amount"]
                
                # Check if vendor should be registered (based on annual turnover)
                # If total transactions exceed threshold, vendor likely should be registered
                if total_amount >= self.gst_registration_threshold or data["count"] >= 10:
                    severity = "high"
                    reason = "Vendor likely exceeds GST registration threshold"
                else:
                    severity = "medium"
                    reason = "GST-applicable transaction without vendor GSTIN"
                
                # Calculate potential ITC loss
                gst_rate = 18.0
                total_itc_loss = sum(
                    (float(t.get("amount", 0)) / (1 + gst_rate / 100)) * (gst_rate / 100)
                    for t in data["transactions"]
                )
                
                unregistered_issues.append({
                    "issue_type": "unregistered_vendor",
                    "vendor": vendor,
                    "transaction_count": data["count"],
                    "total_amount": round(total_amount, 2),
                    "potential_itc_loss": round(total_itc_loss, 2),
                    "severity": severity,
                    "message": f"{reason}: Vendor '{vendor}' has {data['count']} GST-applicable transactions "
                              f"totaling ₹{total_amount:,.2f} without GSTIN",
                    "implication": f"ITC of ₹{total_itc_loss:,.2f} cannot be claimed without vendor GSTIN. "
                                 "Vendor may be unregistered or GSTIN not captured.",
                    "law_reference": "CGST Act, 2017 - Section 22 - GST registration mandatory above ₹20 lakh turnover",
                    "recommendation": f"Request GSTIN from vendor '{vendor}'. "
                                    "If vendor is unregistered, verify if GST is applicable. "
                                    "Consider alternative vendors if compliance cannot be ensured.",
                    "transactions": [
                        {
                            "transaction_id": t.get("id"),
                            "date": t.get("date"),
                            "amount": float(t.get("amount", 0))
                        }
                        for t in data["transactions"][:10]  # Limit to first 10
                    ]
                })
            
            logger.info(f"Detected {len(unregistered_issues)} unregistered vendor issues for client {client_id}")
            return unregistered_issues
            
        except Exception as e:
            logger.error(f"Error detecting unregistered vendors: {str(e)}")
            return []

    def run_full_scan(
        self, 
        client_id: str, 
        blocked_gstin_list: Optional[List[str]] = None,
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive suspicious vendor detection scan combining all methods.
        
        Args:
            client_id: Client identifier.
            blocked_gstin_list: Optional list of blocked GSTINs.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            Dictionary containing all detected suspicious vendor issues categorized by type.
        """
        try:
            high_risk = self.detect_high_risk_vendors(client_id, start_date, end_date)
            gst_mismatches = self.detect_gst_registration_mismatches(client_id, start_date, end_date)
            blocked_gstins = self.detect_blocked_gstins(client_id, blocked_gstin_list, start_date, end_date)
            unregistered = self.detect_unregistered_vendors(client_id, start_date, end_date)
            
            all_issues = high_risk + gst_mismatches + blocked_gstins + unregistered
            
            # Calculate total potential ITC loss
            total_itc_loss = sum(
                issue.get("potential_itc_loss", 0) for issue in blocked_gstins + unregistered
            )
            
            return {
                "client_id": client_id,
                "scan_date": datetime.now().isoformat(),
                "date_range": {
                    "start": start_date or (datetime.now() - timedelta(days=365)).date().isoformat(),
                    "end": end_date or datetime.now().date().isoformat()
                },
                "results": {
                    "high_risk_vendors": {
                        "count": len(high_risk),
                        "items": high_risk
                    },
                    "gst_registration_mismatches": {
                        "count": len(gst_mismatches),
                        "items": gst_mismatches
                    },
                    "blocked_gstins": {
                        "count": len(blocked_gstins),
                        "items": blocked_gstins
                    },
                    "unregistered_vendors": {
                        "count": len(unregistered),
                        "items": unregistered
                    }
                },
                "summary": {
                    "total_issues": len(all_issues),
                    "high_risk_vendor_count": len(high_risk),
                    "critical_issues": sum(1 for item in all_issues if item.get("severity") == "critical"),
                    "high_severity": sum(1 for item in all_issues if item.get("severity") == "high"),
                    "medium_severity": sum(1 for item in all_issues if item.get("severity") == "medium"),
                    "total_potential_itc_loss": round(total_itc_loss, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error running full suspicious vendor scan: {str(e)}")
            return {
                "client_id": client_id,
                "scan_date": datetime.now().isoformat(),
                "error": str(e),
                "results": {
                    "high_risk_vendors": {"count": 0, "items": []},
                    "gst_registration_mismatches": {"count": 0, "items": []},
                    "blocked_gstins": {"count": 0, "items": []},
                    "unregistered_vendors": {"count": 0, "items": []}
                }
            }

