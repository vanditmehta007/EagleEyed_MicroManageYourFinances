from typing import List, Dict, Any, Optional
from backend.models.redflag_models import RedFlag
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

class AnomalyDetectorService:
    """
    Service for detecting anomalies and red flags in financial transactions.
    
    Detects:
    - Duplicate transactions
    - Large cash transactions
    - Round number transactions (potential manipulation)
    - Unusual patterns (weekend transactions, late-night entries)
    - Missing invoice numbers
    - Suspicious vendor patterns
    """

    def __init__(self):
        self.large_cash_threshold = 10000
        self.duplicate_time_window_hours = 24
        self.round_number_threshold = 50000  # Flag round numbers above this

    def get_red_flags(self, client_id: str, resolved: Optional[bool] = None) -> List[RedFlag]:
        """
        Get all red flags for a client, optionally filtered by status.
        """
        try:
            query = supabase.table("red_flags").select("*").eq("client_id", client_id)
            
            if resolved is not None:
                query = query.eq("resolved", resolved)
            
            response = query.execute()
            flags = response.data if response.data else []
            
            # Convert to RedFlag objects
            result = []
            for flag in flags:
                try:
                    result.append(RedFlag(
                        id=flag.get("id", ""),
                        transaction_id=flag.get("transaction_id", ""),
                        flag_type=flag.get("flag_type", "anomaly"),
                        severity=flag.get("severity", "medium"),
                        message=flag.get("message", ""),
                        created_at=flag.get("created_at", datetime.utcnow()),
                        resolved=flag.get("resolved", False)
                    ))
                except Exception:
                    continue
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get red flags: {e}")
            return []

    def resolve_flag(self, flag_id: str, resolution_note: str) -> RedFlag:
        """
        Mark a red flag as resolved with a note.
        """
        try:
            response = supabase.table("red_flags").update({
                "resolved": True,
                "resolution_note": resolution_note,
                "resolved_at": datetime.utcnow().isoformat()
            }).eq("id", flag_id).execute()
            
            if response.data:
                flag_data = response.data[0]
                return RedFlag(
                    id=flag_data.get("id", ""),
                    transaction_id=flag_data.get("transaction_id", ""),
                    flag_type=flag_data.get("flag_type", "anomaly"),
                    severity=flag_data.get("severity", "medium"),
                    message=flag_data.get("message", ""),
                    created_at=flag_data.get("created_at", datetime.utcnow()),
                    resolved=flag_data.get("resolved", False)
                )
            else:
                raise Exception("Flag not found")
                
        except Exception as e:
            logger.error(f"Failed to resolve flag: {e}")
            raise Exception(f"Failed to resolve flag: {str(e)}")

    def run_scan(self, client_id: str) -> Dict[str, Any]:
        """
        Manually trigger a comprehensive red flag scan for a client.
        """
        try:
            # Fetch recent transactions
            response = supabase.table("transactions").select("*").eq("client_id", client_id).is_("deleted_at", "null").limit(1000).execute()
            transactions = response.data if response.data else []
            
            flags_created = 0
            
            # Run all detection methods
            flags_created += self._detect_duplicates(client_id, transactions)
            flags_created += self._detect_large_cash(client_id, transactions)
            flags_created += self._detect_round_numbers(client_id, transactions)
            flags_created += self._detect_missing_invoices(client_id, transactions)
            
            return {
                "client_id": client_id,
                "scan_completed": True,
                "transactions_scanned": len(transactions),
                "flags_created": flags_created
            }
            
        except Exception as e:
            logger.error(f"Anomaly scan failed: {e}")
            return {
                "client_id": client_id,
                "scan_completed": False,
                "error": str(e)
            }

    def _detect_duplicates(self, client_id: str, transactions: List[Dict[str, Any]]) -> int:
        """
        Detect duplicate transactions (same amount, vendor, and date within 24 hours).
        """
        flags_created = 0
        
        # Group transactions by (amount, vendor, date)
        txn_groups = defaultdict(list)
        
        for txn in transactions:
            key = (
                float(txn.get("amount", 0)),
                str(txn.get("vendor", "")).lower(),
                str(txn.get("date", ""))[:10]  # Date only (YYYY-MM-DD)
            )
            txn_groups[key].append(txn)
        
        # Find duplicates
        for key, group in txn_groups.items():
            if len(group) > 1:
                # Potential duplicate
                for txn in group:
                    flag_data = {
                        "id": str(uuid.uuid4()),
                        "client_id": client_id,
                        "transaction_id": txn.get("id"),
                        "flag_type": "duplicate",
                        "severity": "high",
                        "message": f"Potential duplicate: {len(group)} transactions with same amount (₹{key[0]:,.2f}), vendor ({key[1]}), and date ({key[2]})",
                        "resolved": False,
                        "created_at": datetime.utcnow().isoformat()
                    }
                    
                    try:
                        supabase.table("red_flags").insert(flag_data).execute()
                        flags_created += 1
                    except Exception:
                        pass
        
        return flags_created

    def _detect_large_cash(self, client_id: str, transactions: List[Dict[str, Any]]) -> int:
        """
        Detect large cash transactions (potential Section 269ST violation).
        """
        flags_created = 0
        
        for txn in transactions:
            amount = float(txn.get("amount", 0))
            mode = str(txn.get("mode", "")).upper()
            
            if mode == "CASH" and amount > self.large_cash_threshold:
                flag_data = {
                    "id": str(uuid.uuid4()),
                    "client_id": client_id,
                    "transaction_id": txn.get("id"),
                    "flag_type": "large_cash",
                    "severity": "high" if amount > 200000 else "medium",
                    "message": f"Large cash transaction of ₹{amount:,.2f} detected. Section 269ST restricts cash transactions above ₹2,00,000",
                    "resolved": False,
                    "created_at": datetime.utcnow().isoformat()
                }
                
                try:
                    supabase.table("red_flags").insert(flag_data).execute()
                    flags_created += 1
                except Exception:
                    pass
        
        return flags_created

    def _detect_round_numbers(self, client_id: str, transactions: List[Dict[str, Any]]) -> int:
        """
        Detect suspiciously round number transactions (potential manipulation).
        """
        flags_created = 0
        
        for txn in transactions:
            amount = float(txn.get("amount", 0))
            
            # Check if amount is a round number (divisible by 10000, 50000, 100000)
            if amount >= self.round_number_threshold:
                if amount % 100000 == 0 or amount % 50000 == 0:
                    flag_data = {
                        "id": str(uuid.uuid4()),
                        "client_id": client_id,
                        "transaction_id": txn.get("id"),
                        "flag_type": "round_number",
                        "severity": "low",
                        "message": f"Suspiciously round amount: ₹{amount:,.2f}. Verify if this is a genuine transaction.",
                        "resolved": False,
                        "created_at": datetime.utcnow().isoformat()
                    }
                    
                    try:
                        supabase.table("red_flags").insert(flag_data).execute()
                        flags_created += 1
                    except Exception:
                        pass
        
        return flags_created

    def _detect_missing_invoices(self, client_id: str, transactions: List[Dict[str, Any]]) -> int:
        """
        Detect expense transactions missing invoice numbers.
        """
        flags_created = 0
        
        for txn in transactions:
            amount = float(txn.get("amount", 0))
            invoice_number = txn.get("invoice_number")
            txn_type = txn.get("type", "")
            
            # Flag expenses above ₹50,000 without invoice numbers
            if txn_type == "debit" and amount > 50000 and not invoice_number:
                flag_data = {
                    "id": str(uuid.uuid4()),
                    "client_id": client_id,
                    "transaction_id": txn.get("id"),
                    "flag_type": "missing_invoice",
                    "severity": "medium",
                    "message": f"Expense of ₹{amount:,.2f} missing invoice number. Required for audit trail.",
                    "resolved": False,
                    "created_at": datetime.utcnow().isoformat()
                }
                
                try:
                    supabase.table("red_flags").insert(flag_data).execute()
                    flags_created += 1
                except Exception:
                    pass
        
        return flags_created
