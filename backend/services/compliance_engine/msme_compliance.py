from typing import List, Dict, Any
from datetime import datetime, timedelta
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger


class MSMEComplianceService:
    """
    Service for MSME compliance checks.
    Includes payment delay detection, interest applicability, registration validation, and due‑date tracking.
    """

    # MSME payment timeline (days)
    MSME_PAYMENT_DAYS = 45

    # MSME interest rate (3 times bank rate, typically 18% per annum)
    MSME_INTEREST_RATE = 0.18

    def check_msme_status(self, vendor_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Check for MSME payment delays and interest obligations for a list of vendors.
        
        Args:
            vendor_ids: List of vendor IDs to check.
        
        Returns:
            A list of dictionaries containing MSME compliance status for each vendor.
        """
        results = []
        
        if not vendor_ids:
            return results
        
        try:
            # Fetch transactions for these vendors
            # Note: In a full implementation, there would be a vendors table with MSME registration status
            response = supabase.table("transactions").select("*").in_("vendor", vendor_ids).execute()
            transactions = response.data if response.data else []
            
            # Group by vendor
            vendor_transactions = {}
            for txn in transactions:
                vendor = txn.get("vendor")
                if vendor:
                    if vendor not in vendor_transactions:
                        vendor_transactions[vendor] = []
                    vendor_transactions[vendor].append(txn)
            
            # MSME payment rules: Payment should be made within 45 days (or as per agreement)
            # Interest rate: 3 times the bank rate (typically around 18% per annum)
            
            for vendor, txns in vendor_transactions.items():
                total_delayed_amount = 0
                total_interest = 0
                delayed_payments = []
                
                for txn in txns:
                    txn_date = txn.get("date")
                    if txn_date:
                        try:
                            payment_date = datetime.fromisoformat(txn_date.replace('Z', '+00:00'))
                            due_date = payment_date + timedelta(days=self.MSME_PAYMENT_DAYS)  # MSME payment due date
                            
                            if datetime.now() > due_date:
                                amount = float(txn.get("amount", 0))
                                days_delayed = (datetime.now() - due_date).days
                                total_delayed_amount += amount
                                
                                # Calculate interest: 18% per annum (3x bank rate)
                                interest = amount * (self.MSME_INTEREST_RATE / 365) * days_delayed
                                total_interest += interest
                                
                                delayed_payments.append({
                                    "transaction_id": txn.get("id"),
                                    "amount": amount,
                                    "due_date": due_date.isoformat(),
                                    "days_delayed": days_delayed,
                                    "interest": round(interest, 2)
                                })
                        except:
                            pass
                
                if delayed_payments:
                    results.append({
                        "vendor_id": vendor,
                        "vendor_name": vendor,
                        "msme_registered": True,  # Would check from vendors table
                        "total_delayed_amount": round(total_delayed_amount, 2),
                        "total_interest_payable": round(total_interest, 2),
                        "delayed_payments": delayed_payments,
                        "compliance_status": "non_compliant"
                    })
                else:
                    results.append({
                        "vendor_id": vendor,
                        "vendor_name": vendor,
                        "msme_registered": True,
                        "total_delayed_amount": 0,
                        "total_interest_payable": 0,
                        "delayed_payments": [],
                        "compliance_status": "compliant"
                    })
            
        except Exception as e:
            # Return empty results on error
            logger.error(f"MSME status check failed: {e}")
            pass
        
        return results

    def detect_payment_delays(self, client_id: str) -> List[Dict[str, Any]]:
        """
        Detect payments that are delayed beyond MSME‑specified timelines.
        
        Args:
            client_id: Identifier of the client whose payments are being analyzed.
        
        Returns:
            A list of dictionaries describing delayed payments, including invoice ID, due date, actual payment date, and delay duration.
        """
        delayed_payments = []
        
        try:
            # TODO: Retrieve payment records and compare actual dates against MSME deadlines
            # Fetch all sheets for this client
            sheets_response = supabase.table("sheets").select("id").eq("client_id", client_id).is_("deleted_at", "null").execute()
            
            if not sheets_response.data:
                return delayed_payments
            
            sheet_ids = [sheet["id"] for sheet in sheets_response.data]
            
            # Fetch all debit (purchase) transactions
            for sheet_id in sheet_ids:
                transactions_response = supabase.table("transactions").select("*").eq("sheet_id", sheet_id).eq("type", "debit").is_("deleted_at", "null").execute()
                
                if not transactions_response.data:
                    continue
                
                transactions = transactions_response.data
                
                for txn in transactions:
                    txn_date = txn.get("date")
                    vendor = txn.get("vendor")
                    invoice_number = txn.get("invoice_number")
                    
                    if txn_date and vendor:
                        try:
                            # Parse transaction date
                            if isinstance(txn_date, str):
                                payment_date = datetime.fromisoformat(txn_date.replace('Z', '+00:00'))
                            else:
                                payment_date = txn_date
                            
                            # Calculate MSME due date (45 days from transaction)
                            due_date = payment_date + timedelta(days=self.MSME_PAYMENT_DAYS)
                            current_date = datetime.now()
                            
                            # Check if payment is delayed
                            if current_date > due_date:
                                days_delayed = (current_date - due_date).days
                                amount = float(txn.get("amount", 0))
                                
                                delayed_payments.append({
                                    "transaction_id": txn.get("id"),
                                    "invoice_number": invoice_number or "N/A",
                                    "vendor": vendor,
                                    "amount": amount,
                                    "transaction_date": payment_date.isoformat(),
                                    "due_date": due_date.isoformat(),
                                    "actual_payment_date": None,  # Placeholder - would track actual payment
                                    "days_delayed": days_delayed,
                                    "status": "overdue"
                                })
                        except Exception as e:
                            logger.error(f"Error processing transaction {txn.get('id')}: {e}")
                            continue
            
            logger.info(f"Detected {len(delayed_payments)} delayed MSME payments for client {client_id}")
            
        except Exception as e:
            logger.error(f"Payment delay detection failed for client {client_id}: {e}")
        
        return delayed_payments

    def assess_interest_applicability(self, client_id: str) -> List[Dict[str, Any]]:
        """
        Determine whether interest should be applied to delayed payments according to MSME rules.
        
        Args:
            client_id: Identifier of the client.
        
        Returns:
            A list of dictionaries containing payment IDs and calculated interest amounts (if applicable).
        """
        interest_assessments = []
        
        try:
            # TODO: Apply MSME interest rate calculations to delayed payments identified earlier
            # Get all delayed payments first
            delayed_payments = self.detect_payment_delays(client_id)
            
            for payment in delayed_payments:
                amount = payment.get("amount", 0)
                days_delayed = payment.get("days_delayed", 0)
                
                # Calculate interest as per MSME Act
                # Interest = Principal × Rate × (Days Delayed / 365)
                interest_amount = amount * (self.MSME_INTEREST_RATE / 365) * days_delayed
                
                # Interest is applicable if payment is delayed beyond 45 days
                if days_delayed > 0:
                    interest_assessments.append({
                        "transaction_id": payment.get("transaction_id"),
                        "invoice_number": payment.get("invoice_number"),
                        "vendor": payment.get("vendor"),
                        "principal_amount": amount,
                        "days_delayed": days_delayed,
                        "interest_rate": f"{self.MSME_INTEREST_RATE * 100}% per annum",
                        "interest_amount": round(interest_amount, 2),
                        "total_payable": round(amount + interest_amount, 2),
                        "interest_applicable": True,
                        "legal_reference": "MSME Development Act, 2006 - Section 16"
                    })
            
            logger.info(f"Assessed interest for {len(interest_assessments)} delayed payments for client {client_id}")
            
        except Exception as e:
            logger.error(f"Interest assessment failed for client {client_id}: {e}")
        
        return interest_assessments

    def validate_registration(self, client_id: str) -> List[Dict[str, Any]]:
        """
        Validate the client's MSME registration status and required documentation.
        
        Args:
            client_id: Identifier of the client.
        
        Returns:
            A list of validation results, each indicating a registration element and whether it is compliant.
        """
        validation_results = []
        
        try:
            # TODO: Check registration number, certificate validity, and any missing required documents
            # Fetch client details
            client_response = supabase.table("clients").select("*").eq("id", client_id).single().execute()
            
            if not client_response.data:
                return [{
                    "element": "client_record",
                    "status": "not_found",
                    "compliant": False,
                    "message": "Client record not found"
                }]
            
            client = client_response.data
            
            # Check 1: MSME Registration Number (Udyam Registration)
            msme_number = client.get("msme_registration_number")
            if msme_number:
                validation_results.append({
                    "element": "msme_registration_number",
                    "status": "present",
                    "compliant": True,
                    "value": msme_number,
                    "message": "MSME/Udyam registration number found"
                })
            else:
                validation_results.append({
                    "element": "msme_registration_number",
                    "status": "missing",
                    "compliant": False,
                    "message": "MSME/Udyam registration number not found"
                })
            
            # Check 2: MSME Certificate (check documents table)
            documents_response = supabase.table("documents").select("*").eq("client_id", client_id).is_("deleted_at", "null").execute()
            
            has_msme_certificate = False
            if documents_response.data:
                for doc in documents_response.data:
                    folder_category = doc.get("folder_category", "").lower()
                    if "msme" in folder_category or "udyam" in folder_category:
                        has_msme_certificate = True
                        break
            
            if has_msme_certificate:
                validation_results.append({
                    "element": "msme_certificate",
                    "status": "present",
                    "compliant": True,
                    "message": "MSME/Udyam certificate found in documents"
                })
            else:
                validation_results.append({
                    "element": "msme_certificate",
                    "status": "missing",
                    "compliant": False,
                    "message": "MSME/Udyam certificate not found. Please upload."
                })
            
            # Check 3: PAN (required for MSME registration)
            pan = client.get("pan")
            if pan and len(pan) == 10:
                validation_results.append({
                    "element": "pan",
                    "status": "valid",
                    "compliant": True,
                    "message": "Valid PAN found"
                })
            else:
                validation_results.append({
                    "element": "pan",
                    "status": "invalid",
                    "compliant": False,
                    "message": "Valid PAN required for MSME registration"
                })
            
            # Check 4: GSTIN (if applicable)
            gstin = client.get("gstin")
            if gstin and len(gstin) == 15:
                validation_results.append({
                    "element": "gstin",
                    "status": "valid",
                    "compliant": True,
                    "message": "Valid GSTIN found"
                })
            else:
                validation_results.append({
                    "element": "gstin",
                    "status": "missing_or_invalid",
                    "compliant": False,
                    "message": "GSTIN missing or invalid"
                })
            
            logger.info(f"MSME registration validation completed for client {client_id}")
            
        except Exception as e:
            logger.error(f"Registration validation failed for client {client_id}: {e}")
            validation_results.append({
                "element": "validation_process",
                "status": "error",
                "compliant": False,
                "message": f"Validation error: {str(e)}"
            })
        
        return validation_results

    def track_due_dates(self, client_id: str) -> List[Dict[str, Any]]:
        """
        Track upcoming statutory due dates for MSME compliance (e.g., filing deadlines, tax payments).
        
        Args:
            client_id: Identifier of the client.
        
        Returns:
            A list of upcoming due dates with description and days remaining.
        """
        due_dates = []
        
        try:
            # TODO: Compile a calendar of MSME‑related deadlines based on client activities and regulatory calendars
            current_date = datetime.now()
            current_year = current_date.year
            current_month = current_date.month
            
            # MSME-specific statutory due dates
            
            # 1. Half-yearly return filing (if applicable)
            # Due dates: October 31 (for Apr-Sep) and April 30 (for Oct-Mar)
            if current_month <= 10:
                half_year_due = datetime(current_year, 10, 31)
                if half_year_due > current_date:
                    days_remaining = (half_year_due - current_date).days
                    due_dates.append({
                        "due_date": half_year_due.isoformat(),
                        "description": "MSME Half-Yearly Return (Apr-Sep)",
                        "days_remaining": days_remaining,
                        "category": "filing",
                        "priority": "medium" if days_remaining > 30 else "high"
                    })
            
            if current_month > 10 or current_month <= 4:
                half_year_due = datetime(current_year if current_month <= 4 else current_year + 1, 4, 30)
                if half_year_due > current_date:
                    days_remaining = (half_year_due - current_date).days
                    due_dates.append({
                        "due_date": half_year_due.isoformat(),
                        "description": "MSME Half-Yearly Return (Oct-Mar)",
                        "days_remaining": days_remaining,
                        "category": "filing",
                        "priority": "medium" if days_remaining > 30 else "high"
                    })
            
            # 2. Annual return filing
            annual_due = datetime(current_year, 5, 31)
            if annual_due > current_date:
                days_remaining = (annual_due - current_date).days
                due_dates.append({
                    "due_date": annual_due.isoformat(),
                    "description": "MSME Annual Return",
                    "days_remaining": days_remaining,
                    "category": "filing",
                    "priority": "high" if days_remaining <= 30 else "medium"
                })
            
            # 3. Check for pending MSME payments (45-day rule)
            delayed_payments = self.detect_payment_delays(client_id)
            if delayed_payments:
                for payment in delayed_payments[:5]:  # Top 5 most urgent
                    due_dates.append({
                        "due_date": payment.get("due_date"),
                        "description": f"MSME Payment Due - {payment.get('vendor')} (Invoice: {payment.get('invoice_number')})",
                        "days_remaining": -payment.get("days_delayed"),  # Negative indicates overdue
                        "category": "payment",
                        "priority": "critical",
                        "amount": payment.get("amount")
                    })
            
            # Sort by days remaining (most urgent first)
            due_dates.sort(key=lambda x: x["days_remaining"])
            
            logger.info(f"Tracked {len(due_dates)} MSME due dates for client {client_id}")
            
        except Exception as e:
            logger.error(f"Due date tracking failed for client {client_id}: {e}")
        
        return due_dates
