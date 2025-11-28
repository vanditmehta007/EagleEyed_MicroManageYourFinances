# backend/services/ledger_classifier/recurrence_detector.py

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger
import statistics


class RecurrenceDetector:
    """
    Detects recurring transactions (subscriptions, rent, salaries, EMIs, etc.)
    by analyzing historical transaction patterns.
    
    Identifies:
    - Monthly/quarterly/annual recurring expenses
    - Subscription services
    - Regular vendor payments
    - Salary disbursements
    - EMI/loan payments
    
    Uses pattern matching on vendor, amount, and frequency.
    """

    # Subscription service keywords
    SUBSCRIPTION_KEYWORDS = [
        'netflix', 'amazon', 'aws', 'azure', 'google', 'microsoft', 'zoom',
        'slack', 'spotify', 'adobe', 'dropbox', 'github', 'linkedin',
        'salesforce', 'hubspot', 'mailchimp', 'stripe', 'razorpay'
    ]
    
    # Frequency thresholds (in days)
    WEEKLY_RANGE = (5, 9)
    MONTHLY_RANGE = (25, 35)
    QUARTERLY_RANGE = (85, 95)
    ANNUAL_RANGE = (355, 375)

    def __init__(self) -> None:
        # TODO: Initialize database connection for historical transaction queries
        # TODO: Load recurrence detection thresholds and parameters
        self.min_occurrences = 3  # Minimum occurrences to consider recurring
        self.amount_tolerance = 0.1  # 10% tolerance for amount variance
        self.date_tolerance = 5  # Days tolerance for date variance
        logger.info("RecurrenceDetector initialized")

    def detect_recurring_transactions(self, client_id: str, lookback_months: int = 12) -> List[Dict[str, Any]]:
        """
        Identify all recurring transactions for a client.
        """
        # TODO: Fetch all transactions for the client within lookback period
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=lookback_months * 30)).isoformat()
            response = supabase.table("transactions").select("*").eq("client_id", client_id).gte("date", cutoff_date).is_("deleted_at", "null").execute()
            transactions = response.data or []
            
            # TODO: Group transactions by vendor and similar amounts
            vendor_groups = defaultdict(list)
            for txn in transactions:
                vendor = txn.get("vendor", "Unknown")
                vendor_groups[vendor].append(txn)
            
            recurring_patterns = []
            
            for vendor, txns in vendor_groups.items():
                if len(txns) < self.min_occurrences:
                    continue
                
                # TODO: Analyze time intervals between transactions
                # TODO: Identify patterns (monthly, quarterly, annual)
                txns_sorted = sorted(txns, key=lambda x: x.get("date", ""))
                
                # Group by similar amounts
                amount_groups = self._group_by_similar_amounts(txns_sorted)
                
                for amount_group in amount_groups:
                    if len(amount_group) < self.min_occurrences:
                        continue
                    
                    txn_ids = [t["id"] for t in amount_group]
                    frequency = self.get_recurrence_frequency(txn_ids)
                    
                    if frequency != "irregular":
                        avg_amount = statistics.mean([t.get("amount", 0) for t in amount_group])
                        last_date = amount_group[-1].get("date")
                        next_date = self._predict_next_date(last_date, frequency)
                        
                        recurring_patterns.append({
                            "vendor_name": vendor,
                            "average_amount": round(avg_amount, 2),
                            "frequency": frequency,
                            "next_expected_date": next_date,
                            "transaction_ids": txn_ids,
                            "occurrence_count": len(amount_group)
                        })
            
            # TODO: Return list of recurring transaction groups
            logger.info(f"Detected {len(recurring_patterns)} recurring patterns for client {client_id}")
            return recurring_patterns
            
        except Exception as e:
            logger.error(f"Recurrence detection failed: {e}")
            return []

    def is_recurring(self, transaction_id: str) -> bool:
        """
        Check if a specific transaction is part of a recurring pattern.
        """
        # TODO: Fetch transaction details
        try:
            txn_response = supabase.table("transactions").select("*").eq("id", transaction_id).execute()
            if not txn_response.data:
                return False
            
            txn = txn_response.data[0]
            vendor = txn.get("vendor")
            amount = txn.get("amount", 0)
            client_id = txn.get("client_id")
            
            # TODO: Search for similar transactions (same vendor, similar amount)
            similar_response = supabase.table("transactions").select("*").eq("client_id", client_id).eq("vendor", vendor).is_("deleted_at", "null").execute()
            similar_txns = similar_response.data or []
            
            # Filter by similar amount
            similar_txns = [t for t in similar_txns if abs(t.get("amount", 0) - amount) / amount <= self.amount_tolerance]
            
            # TODO: Check if pattern exists (at least 3 occurrences with regular intervals)
            if len(similar_txns) < self.min_occurrences:
                return False
            
            txn_ids = [t["id"] for t in similar_txns]
            frequency = self.get_recurrence_frequency(txn_ids)
            
            # TODO: Return boolean result
            return frequency != "irregular"
            
        except Exception as e:
            logger.error(f"Failed to check recurrence: {e}")
            return False

    def predict_next_occurrence(self, vendor_name: str, client_id: str) -> Optional[datetime]:
        """
        Predict the next expected date for a recurring transaction.
        """
        # TODO: Fetch historical transactions for this vendor
        try:
            response = supabase.table("transactions").select("*").eq("client_id", client_id).eq("vendor", vendor_name).is_("deleted_at", "null").order("date", desc=False).execute()
            transactions = response.data or []
            
            if len(transactions) < 2:
                return None
            
            # TODO: Calculate average interval between transactions
            dates = [datetime.fromisoformat(t["date"]) for t in transactions if t.get("date")]
            intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
            
            if not intervals:
                return None
            
            avg_interval = statistics.mean(intervals)
            
            # TODO: Add interval to last transaction date
            last_date = dates[-1]
            next_date = last_date + timedelta(days=avg_interval)
            
            # TODO: Return predicted date
            return next_date
            
        except Exception as e:
            logger.error(f"Failed to predict next occurrence: {e}")
            return None

    def get_recurrence_frequency(self, transaction_ids: List[str]) -> str:
        """
        Determine the frequency of a recurring transaction pattern.
        """
        # TODO: Fetch transaction dates
        try:
            response = supabase.table("transactions").select("date").in_("id", transaction_ids).order("date", desc=False).execute()
            transactions = response.data or []
            
            if len(transactions) < 2:
                return "irregular"
            
            # TODO: Calculate intervals between consecutive transactions
            dates = [datetime.fromisoformat(t["date"]) for t in transactions if t.get("date")]
            intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
            
            if not intervals:
                return "irregular"
            
            # TODO: Determine most common interval
            avg_interval = statistics.mean(intervals)
            
            # TODO: Map to frequency category
            if self.WEEKLY_RANGE[0] <= avg_interval <= self.WEEKLY_RANGE[1]:
                return "weekly"
            elif self.MONTHLY_RANGE[0] <= avg_interval <= self.MONTHLY_RANGE[1]:
                return "monthly"
            elif self.QUARTERLY_RANGE[0] <= avg_interval <= self.QUARTERLY_RANGE[1]:
                return "quarterly"
            elif self.ANNUAL_RANGE[0] <= avg_interval <= self.ANNUAL_RANGE[1]:
                return "annual"
            
            # TODO: Return frequency string
            return "irregular"
            
        except Exception as e:
            logger.error(f"Failed to determine frequency: {e}")
            return "irregular"

    def detect_subscription_services(self, client_id: str) -> List[Dict[str, Any]]:
        """
        Identify subscription-based services (SaaS, streaming, etc.).
        """
        # TODO: Fetch recurring transactions
        recurring = self.detect_recurring_transactions(client_id, lookback_months=12)
        
        # TODO: Filter for known subscription keywords (Netflix, AWS, Zoom, etc.)
        # TODO: Filter for small, regular amounts (typical of subscriptions)
        subscriptions = []
        for pattern in recurring:
            vendor = pattern["vendor_name"].lower()
            amount = pattern["average_amount"]
            
            # Check for subscription keywords or monthly frequency with reasonable amount
            is_subscription = (
                any(keyword in vendor for keyword in self.SUBSCRIPTION_KEYWORDS) or
                (pattern["frequency"] == "monthly" and amount < 50000)  # Typical subscription range
            )
            
            if is_subscription:
                subscriptions.append({
                    "vendor": pattern["vendor_name"],
                    "amount": pattern["average_amount"],
                    "renewal_date": pattern["next_expected_date"],
                    "frequency": pattern["frequency"]
                })
        
        # TODO: Return subscription list
        logger.info(f"Detected {len(subscriptions)} subscriptions for client {client_id}")
        return subscriptions

    def flag_missed_recurring_payments(self, client_id: str) -> List[Dict[str, Any]]:
        """
        Identify recurring payments that were expected but not made.
        """
        # TODO: Get all recurring transaction patterns
        recurring = self.detect_recurring_transactions(client_id, lookback_months=12)
        missed_payments = []
        
        # TODO: For each pattern, predict next expected date
        for pattern in recurring:
            expected_date_str = pattern.get("next_expected_date")
            if not expected_date_str:
                continue
            
            expected_date = datetime.fromisoformat(expected_date_str)
            today = datetime.utcnow()
            
            # TODO: Check if payment was made within tolerance window
            if expected_date < today - timedelta(days=self.date_tolerance):
                # Check if payment was actually made
                vendor = pattern["vendor_name"]
                amount = pattern["average_amount"]
                
                # Search for payment in tolerance window
                search_start = (expected_date - timedelta(days=self.date_tolerance)).isoformat()
                search_end = (expected_date + timedelta(days=self.date_tolerance)).isoformat()
                
                response = supabase.table("transactions").select("*").eq("client_id", client_id).eq("vendor", vendor).gte("date", search_start).lte("date", search_end).execute()
                
                # TODO: Flag as missed if not found
                if not response.data:
                    missed_payments.append({
                        "vendor": vendor,
                        "expected_date": expected_date_str,
                        "expected_amount": amount,
                        "days_overdue": (today - expected_date).days
                    })
        
        # TODO: Return list of missed payments
        logger.info(f"Flagged {len(missed_payments)} missed payments for client {client_id}")
        return missed_payments

    def calculate_recurrence_confidence(self, transaction_ids: List[str]) -> float:
        """
        Calculate confidence score for a recurrence pattern.
        """
        # TODO: Calculate variance in amounts (lower variance = higher confidence)
        # TODO: Calculate variance in intervals (lower variance = higher confidence)
        # TODO: Consider number of occurrences (more occurrences = higher confidence)
        try:
            response = supabase.table("transactions").select("amount, date").in_("id", transaction_ids).order("date", desc=False).execute()
            transactions = response.data or []
            
            if len(transactions) < 2:
                return 0.0
            
            amounts = [t.get("amount", 0) for t in transactions]
            dates = [datetime.fromisoformat(t["date"]) for t in transactions if t.get("date")]
            
            # Amount variance score
            if statistics.mean(amounts) > 0:
                amount_cv = statistics.stdev(amounts) / statistics.mean(amounts)
                amount_score = max(0, 1 - amount_cv)
            else:
                amount_score = 0
            
            # Interval variance score
            intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
            if intervals and statistics.mean(intervals) > 0:
                interval_cv = statistics.stdev(intervals) / statistics.mean(intervals)
                interval_score = max(0, 1 - interval_cv)
            else:
                interval_score = 0
            
            # Occurrence count score
            count_score = min(1.0, len(transactions) / 10)
            
            # TODO: Return normalized confidence score
            confidence = (amount_score * 0.4 + interval_score * 0.4 + count_score * 0.2)
            return round(confidence, 2)
            
        except Exception as e:
            logger.error(f"Failed to calculate confidence: {e}")
            return 0.0

    def _group_by_similar_amounts(self, transactions: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Helper to group transactions by similar amounts."""
        if not transactions:
            return []
        
        groups = []
        for txn in transactions:
            amount = txn.get("amount", 0)
            placed = False
            
            for group in groups:
                group_avg = statistics.mean([t.get("amount", 0) for t in group])
                if abs(amount - group_avg) / group_avg <= self.amount_tolerance:
                    group.append(txn)
                    placed = True
                    break
            
            if not placed:
                groups.append([txn])
        
        return groups

    def _predict_next_date(self, last_date_str: str, frequency: str) -> str:
        """Helper to predict next occurrence date based on frequency."""
        try:
            last_date = datetime.fromisoformat(last_date_str)
            
            if frequency == "weekly":
                next_date = last_date + timedelta(days=7)
            elif frequency == "monthly":
                next_date = last_date + timedelta(days=30)
            elif frequency == "quarterly":
                next_date = last_date + timedelta(days=90)
            elif frequency == "annual":
                next_date = last_date + timedelta(days=365)
            else:
                return ""
            
            return next_date.isoformat()
        except:
            return ""
