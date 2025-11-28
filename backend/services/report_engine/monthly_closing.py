from typing import Dict, Any, List, Optional
from datetime import date, datetime
from backend.utils.date_utils import DateUtils
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger
from collections import defaultdict
from backend.services.document_intake.bank_statement_parser import BankStatementParser

class MonthlyClosingService:
    """
    Service for generating Monthly Closing Reports.
    """

    def __init__(self):
        self.bank_parser = BankStatementParser()

    def generate_closing_report(self, client_id: str, month: int, year: int) -> Dict[str, Any]:
        """
        Generates a comprehensive monthly closing report.
        """
        logger.info(f"Generating monthly closing report for client {client_id} ({month}/{year})")
        
        start_date, end_date = DateUtils.get_month_range(month, year)
        
        report = {
            "client_id": client_id,
            "period": f"{month:02d}-{year}",
            "generated_at": str(date.today()),
            "bank_reconciliation": self._generate_bank_reconciliation(client_id, start_date, end_date),
            "gst_summary": self._generate_gst_summary(client_id, start_date, end_date),
            "itc_snapshot": self._generate_itc_snapshot(client_id, start_date, end_date),
            "debtors_creditors": self._generate_debtor_creditor_list(client_id, end_date),
            "ledger_roll_forward": self._generate_ledger_roll_forward(client_id, start_date, end_date)
        }
        
        return report

    def _generate_bank_reconciliation(self, client_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Generates Bank Reconciliation Statement (BRS).
        """
        try:
            # Fetch book balance (Bank/Cash ledger)
            response = supabase.table("transactions").select("*").eq("client_id", client_id).lte("date", str(end_date)).is_("deleted_at", "null").execute()
            transactions = response.data if response.data else []
            
            book_balance = 0.0
            for txn in transactions:
                ledger = str(txn.get("ledger", "")).lower()
                if "bank" in ledger or "cash" in ledger:
                    amount = float(txn.get("amount", 0))
                    if txn.get("type") == "credit":
                        book_balance += amount
                    else:
                        book_balance -= amount
            
            # Fetch latest bank statement balance
            # Assuming bank statements are uploaded as documents and parsed
            # We look for a bank statement document for this month
            docs_response = supabase.table("documents").select("*").eq("client_id", client_id).eq("folder_category", "bank_statements").gte("created_at", str(start_date)).lte("created_at", str(end_date)).order("created_at", desc=True).limit(1).execute()
            
            bank_balance = book_balance # Default if no statement found
            unreconciled_items = []
            
            if docs_response.data:
                # In a real scenario, we would parse the file content
                # For now, we simulate extracting the closing balance if stored in metadata
                doc = docs_response.data[0]
                metadata = doc.get("metadata", {})
                if "closing_balance" in metadata:
                    bank_balance = float(metadata["closing_balance"])
            
            difference = bank_balance - book_balance
            
            return {
                "bank_balance": round(bank_balance, 2),
                "book_balance": round(book_balance, 2),
                "difference": round(difference, 2),
                "unreconciled_items": unreconciled_items,
                "status": "reconciled" if abs(difference) < 0.01 else "unreconciled"
            }
            
        except Exception as e:
            logger.error(f"Bank reconciliation failed: {e}")
            return {"bank_balance": 0.0, "book_balance": 0.0, "difference": 0.0, "unreconciled_items": []}

    def _generate_gst_summary(self, client_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Generates GST Output vs Input Summary.
        """
        try:
            response = supabase.table("transactions").select("*").eq("client_id", client_id).gte("date", str(start_date)).lte("date", str(end_date)).is_("deleted_at", "null").execute()
            transactions = response.data if response.data else []
            
            output_tax = 0.0
            input_tax = 0.0
            
            for txn in transactions:
                amount = float(txn.get("amount", 0))
                txn_type = txn.get("type", "")
                gst_rate = float(txn.get("gst_rate", 0))
                gst_amount = amount * gst_rate / (100 + gst_rate) if gst_rate > 0 else 0
                
                if txn_type == "credit": output_tax += gst_amount
                elif txn_type == "debit": input_tax += gst_amount
            
            net_payable = output_tax - input_tax
            
            return {
                "output_tax": {"total": round(output_tax, 2)},
                "input_tax": {"total": round(input_tax, 2)},
                "net_payable": round(net_payable, 2)
            }
        except Exception as e:
            logger.error(f"GST summary failed: {e}")
            return {"output_tax": {"total": 0.0}, "input_tax": {"total": 0.0}, "net_payable": 0.0}

    def _generate_itc_snapshot(self, client_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Generates ITC Snapshot.
        """
        try:
            from backend.services.compliance_engine.gst_compliance import GSTComplianceService
            gst_service = GSTComplianceService()
            
            response = supabase.table("transactions").select("*").eq("client_id", client_id).gte("date", str(start_date)).lte("date", str(end_date)).eq("type", "debit").is_("deleted_at", "null").execute()
            transactions = response.data if response.data else []
            
            total_itc = 0.0
            eligible_itc = 0.0
            ineligible_itc = 0.0
            
            for txn in transactions:
                amount = float(txn.get("amount", 0))
                gst_rate = float(txn.get("gst_rate", 0))
                gst_amount = amount * gst_rate / (100 + gst_rate) if gst_rate > 0 else 0
                
                total_itc += gst_amount
                compliance = gst_service._check_transaction_compliance(txn)
                
                if compliance.itc_eligible: eligible_itc += gst_amount
                else: ineligible_itc += gst_amount
            
            return {
                "total_itc_available": round(total_itc, 2),
                "eligible_itc": round(eligible_itc, 2),
                "ineligible_itc": round(ineligible_itc, 2)
            }
        except Exception as e:
            logger.error(f"ITC snapshot failed: {e}")
            return {"total_itc_available": 0.0, "eligible_itc": 0.0, "ineligible_itc": 0.0}

    def _generate_debtor_creditor_list(self, client_id: str, as_of_date: date) -> Dict[str, Any]:
        """
        Generates Debtor and Creditor aging list.
        """
        try:
            # Fetch all unpaid invoices (transactions with status 'pending' or 'partial')
            # Assuming 'payment_status' field exists
            response = supabase.table("transactions").select("*").eq("client_id", client_id).lte("date", str(as_of_date)).neq("payment_status", "paid").is_("deleted_at", "null").execute()
            transactions = response.data if response.data else []
            
            debtors = defaultdict(float)
            creditors = defaultdict(float)
            
            for txn in transactions:
                amount = float(txn.get("amount", 0))
                party = txn.get("vendor") or txn.get("customer_name") or "Unknown"
                txn_type = txn.get("type")
                
                if txn_type == "credit": # Sales -> Debtor
                    debtors[party] += amount
                elif txn_type == "debit": # Purchase -> Creditor
                    creditors[party] += amount
            
            return {
                "debtors": {
                    "total_outstanding": round(sum(debtors.values()), 2),
                    "list": [{"name": k, "amount": round(v, 2)} for k, v in debtors.items()]
                },
                "creditors": {
                    "total_outstanding": round(sum(creditors.values()), 2),
                    "list": [{"name": k, "amount": round(v, 2)} for k, v in creditors.items()]
                }
            }
        except Exception as e:
            logger.error(f"Debtor/Creditor list failed: {e}")
            return {"debtors": {"total_outstanding": 0.0}, "creditors": {"total_outstanding": 0.0}}

    def _generate_ledger_roll_forward(self, client_id: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        Generates Ledger Roll-forward.
        """
        try:
            opening_response = supabase.table("transactions").select("*").eq("client_id", client_id).lt("date", str(start_date)).is_("deleted_at", "null").execute()
            opening_txns = opening_response.data if opening_response.data else []
            
            period_response = supabase.table("transactions").select("*").eq("client_id", client_id).gte("date", str(start_date)).lte("date", str(end_date)).is_("deleted_at", "null").execute()
            period_txns = period_response.data if period_response.data else []
            
            ledger_data = defaultdict(lambda: {"opening": 0.0, "debit": 0.0, "credit": 0.0})
            
            for txn in opening_txns:
                ledger = txn.get("ledger", "Uncategorized")
                amt = float(txn.get("amount", 0))
                if txn.get("type") == "debit": ledger_data[ledger]["opening"] += amt
                else: ledger_data[ledger]["opening"] -= amt
            
            for txn in period_txns:
                ledger = txn.get("ledger", "Uncategorized")
                amt = float(txn.get("amount", 0))
                if txn.get("type") == "debit": ledger_data[ledger]["debit"] += amt
                else: ledger_data[ledger]["credit"] += amt
            
            result = []
            for ledger, data in ledger_data.items():
                closing = data["opening"] + data["debit"] - data["credit"]
                result.append({
                    "ledger": ledger,
                    "opening_balance": round(data["opening"], 2),
                    "debit": round(data["debit"], 2),
                    "credit": round(data["credit"], 2),
                    "closing_balance": round(closing, 2)
                })
            
            return sorted(result, key=lambda x: x["ledger"])
            
        except Exception as e:
            logger.error(f"Ledger roll-forward failed: {e}")
            return []
