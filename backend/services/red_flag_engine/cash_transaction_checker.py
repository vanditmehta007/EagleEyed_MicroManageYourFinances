from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from backend.utils.supabase_client import supabase
from backend.config import settings
from backend.utils.logger import logger


class CashTransactionChecker:
    """
    Service for detecting cash transaction anomalies and IT Act 40A(3) violations.
    
    Detects:
    - Large cash transactions (above threshold)
    - Suspicious cash withdrawal patterns
    - IT Act Section 40A(3) violations (cash payments > ₹10,000 in single day to same person)
    """

    def __init__(self):
        self.cash_limit = settings.CASH_PAYMENT_LIMIT  # ₹10,000 default
        self.suspicious_threshold = 9000.0  # Just below limit - suspicious pattern
        self.large_cash_threshold = 50000.0  # Large cash transaction threshold

    def detect_large_cash_transactions(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect large cash transactions that may require attention.
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD). If not provided, checks last 30 days.
            end_date: Optional end date (YYYY-MM-DD). If not provided, uses today.
            
        Returns:
            List of dictionaries containing transaction details and flags.
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().date().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).date().isoformat()
            
            # Fetch cash transactions
            response = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).eq("mode", "CASH").gte("date", start_date).lte("date", end_date).is_(
                "deleted_at", "null"
            ).execute()
            
            transactions = response.data if response.data else []
            large_transactions = []
            
            for txn in transactions:
                amount = float(txn.get("amount", 0))
                
                # Flag transactions above the cash payment limit
                if amount > self.cash_limit:
                    severity = "high" if amount > self.large_cash_threshold else "medium"
                    
                    large_transactions.append({
                        "transaction_id": txn.get("id"),
                        "date": txn.get("date"),
                        "amount": amount,
                        "vendor": txn.get("vendor"),
                        "description": txn.get("description"),
                        "severity": severity,
                        "violation_type": "large_cash",
                        "message": f"Large cash transaction of ₹{amount:,.2f} detected. "
                                  f"Exceeds IT Act 40A(3) limit of ₹{self.cash_limit:,.0f}",
                        "law_reference": "Income Tax Act, 1961 - Section 40A(3)"
                    })
            
            logger.info(f"Detected {len(large_transactions)} large cash transactions for client {client_id}")
            return large_transactions
            
        except Exception as e:
            logger.error(f"Error detecting large cash transactions: {str(e)}")
            return []

    def detect_suspicious_cash_withdrawals(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect suspicious cash withdrawal patterns.
        
        Patterns detected:
        - Multiple withdrawals just below threshold (potential structuring)
        - Large cash withdrawals
        - Frequent cash withdrawals in short periods
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            List of dictionaries containing suspicious withdrawal patterns.
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().date().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).date().isoformat()
            
            # Fetch cash transactions (debit type for withdrawals)
            response = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).eq("mode", "CASH").eq("type", "debit").gte("date", start_date).lte(
                "date", end_date
            ).is_("deleted_at", "null").order("date").execute()
            
            transactions = response.data if response.data else []
            suspicious_patterns = []
            
            # Group transactions by date
            transactions_by_date = {}
            for txn in transactions:
                date = txn.get("date")
                if date not in transactions_by_date:
                    transactions_by_date[date] = []
                transactions_by_date[date].append(txn)
            
            # Pattern 1: Multiple transactions just below threshold on same day (structuring)
            for date, txns in transactions_by_date.items():
                if len(txns) >= 2:
                    total_amount = sum(float(t.get("amount", 0)) for t in txns)
                    amounts = [float(t.get("amount", 0)) for t in txns]
                    
                    # Check if multiple transactions are just below threshold
                    below_threshold_count = sum(1 for amt in amounts if self.suspicious_threshold <= amt < self.cash_limit)
                    
                    if below_threshold_count >= 2 and total_amount > self.cash_limit:
                        suspicious_patterns.append({
                            "pattern_type": "structuring",
                            "date": date,
                            "transaction_count": len(txns),
                            "total_amount": total_amount,
                            "transactions": [
                                {
                                    "transaction_id": t.get("id"),
                                    "amount": float(t.get("amount", 0)),
                                    "description": t.get("description")
                                }
                                for t in txns
                            ],
                            "severity": "high",
                            "message": f"Suspicious pattern: {len(txns)} cash transactions totaling "
                                      f"₹{total_amount:,.2f} on {date}. Possible structuring to avoid "
                                      f"Section 40A(3) limit.",
                            "law_reference": "Income Tax Act, 1961 - Section 40A(3)"
                        })
            
            # Pattern 2: Large cash withdrawals
            for txn in transactions:
                amount = float(txn.get("amount", 0))
                if amount > self.large_cash_threshold:
                    suspicious_patterns.append({
                        "pattern_type": "large_withdrawal",
                        "transaction_id": txn.get("id"),
                        "date": txn.get("date"),
                        "amount": amount,
                        "description": txn.get("description"),
                        "severity": "medium",
                        "message": f"Large cash withdrawal of ₹{amount:,.2f} detected on {txn.get('date')}",
                        "law_reference": "Income Tax Act, 1961 - Section 40A(3)"
                    })
            
            # Pattern 3: Frequent withdrawals in short period (last 7 days)
            recent_date = (datetime.now() - timedelta(days=7)).date().isoformat()
            recent_txns = [t for t in transactions if t.get("date") >= recent_date]
            
            if len(recent_txns) >= 5:
                total_recent = sum(float(t.get("amount", 0)) for t in recent_txns)
                suspicious_patterns.append({
                    "pattern_type": "frequent_withdrawals",
                    "period": "7_days",
                    "transaction_count": len(recent_txns),
                    "total_amount": total_recent,
                    "severity": "medium",
                    "message": f"Frequent cash withdrawals: {len(recent_txns)} transactions totaling "
                              f"₹{total_recent:,.2f} in the last 7 days",
                    "law_reference": "Income Tax Act, 1961 - Section 40A(3)"
                })
            
            logger.info(f"Detected {len(suspicious_patterns)} suspicious cash withdrawal patterns for client {client_id}")
            return suspicious_patterns
            
        except Exception as e:
            logger.error(f"Error detecting suspicious cash withdrawals: {str(e)}")
            return []

    def detect_40a3_violations(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect IT Act Section 40A(3) violations.
        
        Section 40A(3) states: No deduction shall be allowed for any expenditure
        in excess of ₹10,000 paid otherwise than by an account payee cheque or
        account payee bank draft or use of electronic clearing system.
        
        This method detects:
        - Cash payments > ₹10,000 in a single day to the same person/vendor
        - Multiple cash payments to same vendor on same day exceeding limit
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            List of dictionaries containing 40A(3) violation details.
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().date().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=90)).date().isoformat()  # Check last 3 months
            
            # Fetch cash transactions (debit type for payments)
            response = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).eq("mode", "CASH").eq("type", "debit").gte("date", start_date).lte(
                "date", end_date
            ).is_("deleted_at", "null").order("date").execute()
            
            transactions = response.data if response.data else []
            violations = []
            
            # Group by date and vendor
            transactions_by_date_vendor = {}
            for txn in transactions:
                date = txn.get("date")
                vendor = txn.get("vendor") or "Unknown"
                key = f"{date}_{vendor}"
                
                if key not in transactions_by_date_vendor:
                    transactions_by_date_vendor[key] = []
                transactions_by_date_vendor[key].append(txn)
            
            # Check for violations
            for key, txns in transactions_by_date_vendor.items():
                date, vendor = key.split("_", 1)
                total_amount = sum(float(t.get("amount", 0)) for t in txns)
                
                # Single transaction violation
                if len(txns) == 1 and total_amount > self.cash_limit:
                    txn = txns[0]
                    violations.append({
                        "violation_type": "single_transaction",
                        "transaction_id": txn.get("id"),
                        "date": date,
                        "vendor": vendor,
                        "amount": total_amount,
                        "severity": "high",
                        "message": f"IT Act 40A(3) violation: Cash payment of ₹{total_amount:,.2f} to "
                                  f"'{vendor}' on {date}. Exceeds limit of ₹{self.cash_limit:,.0f}.",
                        "law_reference": "Income Tax Act, 1961 - Section 40A(3)",
                        "disallowance_applicable": True,
                        "disallowance_reason": "Payment made in cash exceeding ₹10,000 limit. "
                                              "Expense may be disallowed for income tax purposes."
                    })
                
                # Multiple transactions to same vendor on same day
                elif len(txns) > 1 and total_amount > self.cash_limit:
                    violations.append({
                        "violation_type": "aggregate_same_day",
                        "date": date,
                        "vendor": vendor,
                        "transaction_count": len(txns),
                        "total_amount": total_amount,
                        "transactions": [
                            {
                                "transaction_id": t.get("id"),
                                "amount": float(t.get("amount", 0)),
                                "description": t.get("description")
                            }
                            for t in txns
                        ],
                        "severity": "high",
                        "message": f"IT Act 40A(3) violation: Aggregate cash payments of ₹{total_amount:,.2f} "
                                  f"to '{vendor}' on {date} across {len(txns)} transactions. "
                                  f"Exceeds limit of ₹{self.cash_limit:,.0f}.",
                        "law_reference": "Income Tax Act, 1961 - Section 40A(3)",
                        "disallowance_applicable": True,
                        "disallowance_reason": "Multiple cash payments to same person on same day "
                                              "exceeding ₹10,000 limit. Expense may be disallowed."
                    })
            
            logger.info(f"Detected {len(violations)} Section 40A(3) violations for client {client_id}")
            return violations
            
        except Exception as e:
            logger.error(f"Error detecting 40A(3) violations: {str(e)}")
            return []

    def run_full_scan(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a comprehensive cash transaction scan combining all detection methods.
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            Dictionary containing all detected issues categorized by type.
        """
        try:
            large_cash = self.detect_large_cash_transactions(client_id, start_date, end_date)
            suspicious = self.detect_suspicious_cash_withdrawals(client_id, start_date, end_date)
            violations = self.detect_40a3_violations(client_id, start_date, end_date)
            
            return {
                "client_id": client_id,
                "scan_date": datetime.now().isoformat(),
                "date_range": {
                    "start": start_date or (datetime.now() - timedelta(days=30)).date().isoformat(),
                    "end": end_date or datetime.now().date().isoformat()
                },
                "results": {
                    "large_cash_transactions": {
                        "count": len(large_cash),
                        "items": large_cash
                    },
                    "suspicious_withdrawals": {
                        "count": len(suspicious),
                        "items": suspicious
                    },
                    "section_40a3_violations": {
                        "count": len(violations),
                        "items": violations
                    }
                },
                "summary": {
                    "total_issues": len(large_cash) + len(suspicious) + len(violations),
                    "high_severity": sum(1 for item in large_cash + suspicious + violations 
                                        if item.get("severity") == "high"),
                    "medium_severity": sum(1 for item in large_cash + suspicious + violations 
                                          if item.get("severity") == "medium"),
                    "low_severity": sum(1 for item in large_cash + suspicious + violations 
                                       if item.get("severity") == "low")
                }
            }
            
        except Exception as e:
            logger.error(f"Error running full cash transaction scan: {str(e)}")
            return {
                "client_id": client_id,
                "scan_date": datetime.now().isoformat(),
                "error": str(e),
                "results": {
                    "large_cash_transactions": {"count": 0, "items": []},
                    "suspicious_withdrawals": {"count": 0, "items": []},
                    "section_40a3_violations": {"count": 0, "items": []}
                }
            }

