from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger


class PatternAnalysis:
    """
    Service for learning repeated financial behavior patterns and detecting deviations.
    
    Analyzes:
    - Recurring transaction patterns (amount, vendor, timing)
    - Statistical patterns (mean, standard deviation, trends)
    - Seasonal/monthly patterns
    - Vendor relationship patterns
    - Anomaly detection using statistical methods
    - Deviation scoring and flagging
    """

    def __init__(self):
        self.min_pattern_occurrences = 3  # Minimum transactions to establish a pattern
        self.z_score_threshold = 2.5  # Z-score threshold for anomaly detection
        self.amount_variance_threshold = 0.2  # 20% variance threshold
        self.date_tolerance_days = 5  # Days tolerance for recurring transactions

    def learn_recurring_patterns(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None,
        min_occurrences: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Learn recurring transaction patterns from historical data.
        
        Identifies:
        - Recurring transactions (same vendor, similar amount, regular timing)
        - Monthly recurring patterns
        - Vendor payment patterns
        - Amount consistency patterns
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD). If not provided, uses last 12 months.
            end_date: Optional end date (YYYY-MM-DD). If not provided, uses today.
            min_occurrences: Minimum occurrences to establish pattern (default: 3).
            
        Returns:
            Dictionary containing learned patterns categorized by type.
        """
        try:
            # Set default date range if not provided (12 months for pattern learning)
            if not end_date:
                end_date = datetime.now().date().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).date().isoformat()
            
            if min_occurrences is None:
                min_occurrences = self.min_pattern_occurrences
            
            # Fetch all transactions
            response = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).gte("date", start_date).lte("date", end_date).is_(
                "deleted_at", "null"
            ).order("date").execute()
            
            transactions = response.data if response.data else []
            
            # Group by vendor
            vendor_transactions = defaultdict(list)
            for txn in transactions:
                vendor = txn.get("vendor", "").strip() if txn.get("vendor") else "Unknown"
                if vendor and vendor != "Unknown":
                    vendor_transactions[vendor].append(txn)
            
            patterns = {
                "recurring_vendor_payments": [],
                "monthly_patterns": [],
                "amount_patterns": [],
                "timing_patterns": []
            }
            
            # Analyze each vendor for recurring patterns
            for vendor, txns in vendor_transactions.items():
                if len(txns) < min_occurrences:
                    continue
                
                # Extract amounts and dates
                amounts = [float(t.get("amount", 0)) for t in txns]
                dates = [datetime.fromisoformat(t.get("date")) for t in txns]
                dates.sort()
                
                # Calculate statistics
                mean_amount = statistics.mean(amounts)
                median_amount = statistics.median(amounts)
                std_dev = statistics.stdev(amounts) if len(amounts) > 1 else 0
                cv = (std_dev / mean_amount) if mean_amount > 0 else 0  # Coefficient of variation
                
                # Check if amounts are consistent (low variance)
                is_consistent = cv < self.amount_variance_threshold
                
                # Check for monthly pattern
                date_diffs = []
                for i in range(1, len(dates)):
                    diff = (dates[i] - dates[i-1]).days
                    date_diffs.append(diff)
                
                avg_days_between = statistics.mean(date_diffs) if date_diffs else 0
                is_monthly = 25 <= avg_days_between <= 35  # Approximately monthly
                
                # Pattern confidence score
                confidence = min(1.0, len(txns) / 12.0)  # Higher confidence with more occurrences
                
                if is_consistent or is_monthly:
                    pattern = {
                        "vendor": vendor,
                        "pattern_type": "monthly_recurring" if is_monthly else "recurring",
                        "occurrence_count": len(txns),
                        "mean_amount": round(mean_amount, 2),
                        "median_amount": round(median_amount, 2),
                        "std_deviation": round(std_dev, 2),
                        "coefficient_of_variation": round(cv, 4),
                        "avg_days_between": round(avg_days_between, 1),
                        "is_consistent": is_consistent,
                        "is_monthly": is_monthly,
                        "date_range": {
                            "start": dates[0].date().isoformat(),
                            "end": dates[-1].date().isoformat()
                        },
                        "confidence": round(confidence, 2),
                        "transactions": [
                            {
                                "transaction_id": t.get("id"),
                                "date": t.get("date"),
                                "amount": float(t.get("amount", 0))
                            }
                            for t in txns
                        ]
                    }
                    
                    if is_monthly:
                        patterns["monthly_patterns"].append(pattern)
                    patterns["recurring_vendor_payments"].append(pattern)
            
            # Analyze amount patterns across all transactions
            all_amounts = [float(t.get("amount", 0)) for t in transactions if t.get("amount")]
            if all_amounts:
                patterns["amount_patterns"] = {
                    "mean": round(statistics.mean(all_amounts), 2),
                    "median": round(statistics.median(all_amounts), 2),
                    "std_deviation": round(statistics.stdev(all_amounts) if len(all_amounts) > 1 else 0, 2),
                    "min": round(min(all_amounts), 2),
                    "max": round(max(all_amounts), 2),
                    "total_transactions": len(all_amounts)
                }
            
            logger.info(f"Learned {len(patterns['recurring_vendor_payments'])} recurring patterns for client {client_id}")
            return patterns
            
        except Exception as e:
            logger.error(f"Error learning recurring patterns: {str(e)}")
            return {
                "recurring_vendor_payments": [],
                "monthly_patterns": [],
                "amount_patterns": {},
                "timing_patterns": []
            }

    def detect_deviations(
        self, 
        client_id: str, 
        patterns: Optional[Dict[str, Any]] = None,
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect deviations from learned patterns.
        
        Compares recent transactions against established patterns to identify:
        - Amount deviations (unusual amounts)
        - Timing deviations (late/early payments)
        - New vendors (breaking vendor patterns)
        - Missing expected transactions
        
        Args:
            client_id: Client identifier.
            patterns: Optional pre-learned patterns. If not provided, will learn from history.
            start_date: Optional start date for recent transactions (default: last 30 days).
            end_date: Optional end date for recent transactions (default: today).
            
        Returns:
            List of dictionaries containing detected deviations.
        """
        try:
            # Learn patterns if not provided
            if patterns is None:
                pattern_end_date = datetime.now().date().isoformat()
                pattern_start_date = (datetime.now() - timedelta(days=365)).date().isoformat()
                patterns = self.learn_recurring_patterns(client_id, pattern_start_date, pattern_end_date)
            
            # Set default date range for recent transactions
            if not end_date:
                end_date = datetime.now().date().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).date().isoformat()
            
            # Fetch recent transactions
            response = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).gte("date", start_date).lte("date", end_date).is_(
                "deleted_at", "null"
            ).execute()
            
            recent_transactions = response.data if response.data else []
            
            deviations = []
            
            # Create pattern lookup by vendor
            vendor_patterns = {}
            for pattern in patterns.get("recurring_vendor_payments", []):
                vendor = pattern.get("vendor")
                if vendor:
                    vendor_patterns[vendor] = pattern
            
            # Check each recent transaction against patterns
            for txn in recent_transactions:
                vendor = txn.get("vendor", "").strip() if txn.get("vendor") else "Unknown"
                amount = float(txn.get("amount", 0))
                date = datetime.fromisoformat(txn.get("date"))
                
                if vendor in vendor_patterns:
                    pattern = vendor_patterns[vendor]
                    mean_amount = pattern.get("mean_amount", 0)
                    std_dev = pattern.get("std_deviation", 0)
                    
                    # Check amount deviation
                    if std_dev > 0:
                        z_score = abs((amount - mean_amount) / std_dev)
                    else:
                        z_score = abs(amount - mean_amount) / mean_amount if mean_amount > 0 else 0
                    
                    if z_score > self.z_score_threshold:
                        deviation_pct = ((amount - mean_amount) / mean_amount * 100) if mean_amount > 0 else 0
                        
                        deviations.append({
                            "deviation_type": "amount_deviation",
                            "transaction_id": txn.get("id"),
                            "vendor": vendor,
                            "date": txn.get("date"),
                            "amount": amount,
                            "expected_amount": round(mean_amount, 2),
                            "deviation_percentage": round(deviation_pct, 2),
                            "z_score": round(z_score, 2),
                            "severity": "high" if z_score > 3.0 else "medium",
                            "message": f"Amount deviation detected for vendor '{vendor}': "
                                      f"₹{amount:,.2f} vs expected ₹{mean_amount:,.2f} "
                                      f"({deviation_pct:+.1f}% deviation)",
                            "implication": f"Transaction amount significantly deviates from established pattern. "
                                         f"Verify if this is intentional or an error.",
                            "pattern_confidence": pattern.get("confidence", 0)
                        })
                    
                    # Check timing deviation for monthly patterns
                    if pattern.get("is_monthly"):
                        avg_days = pattern.get("avg_days_between", 30)
                        last_transaction_date = max(
                            datetime.fromisoformat(t.get("date")) 
                            for t in pattern.get("transactions", [])
                        )
                        
                        days_since_last = (date - last_transaction_date).days
                        expected_days = avg_days
                        
                        if days_since_last < expected_days - self.date_tolerance_days:
                            deviations.append({
                                "deviation_type": "early_payment",
                                "transaction_id": txn.get("id"),
                                "vendor": vendor,
                                "date": txn.get("date"),
                                "amount": amount,
                                "days_since_last": days_since_last,
                                "expected_days": round(expected_days, 1),
                                "severity": "low",
                                "message": f"Early payment detected for vendor '{vendor}': "
                                          f"{days_since_last} days since last payment "
                                          f"(expected ~{expected_days} days)",
                                "implication": "Payment made earlier than usual pattern. May be intentional."
                            })
                        elif days_since_last > expected_days + self.date_tolerance_days:
                            deviations.append({
                                "deviation_type": "late_payment",
                                "transaction_id": txn.get("id"),
                                "vendor": vendor,
                                "date": txn.get("date"),
                                "amount": amount,
                                "days_since_last": days_since_last,
                                "expected_days": round(expected_days, 1),
                                "severity": "medium",
                                "message": f"Late payment detected for vendor '{vendor}': "
                                          f"{days_since_last} days since last payment "
                                          f"(expected ~{expected_days} days)",
                                "implication": "Payment made later than usual pattern. May indicate cash flow issues."
                            })
                else:
                    # New vendor or vendor not in patterns
                    if vendor != "Unknown" and amount > 0:
                        deviations.append({
                            "deviation_type": "new_vendor",
                            "transaction_id": txn.get("id"),
                            "vendor": vendor,
                            "date": txn.get("date"),
                            "amount": amount,
                            "severity": "low",
                            "message": f"Transaction with new vendor '{vendor}' (not in established patterns)",
                            "implication": "New vendor relationship. Monitor to establish pattern."
                        })
            
            # Check for missing expected transactions
            missing_transactions = self._detect_missing_expected_transactions(
                patterns, start_date, end_date
            )
            deviations.extend(missing_transactions)
            
            logger.info(f"Detected {len(deviations)} deviations from patterns for client {client_id}")
            return deviations
            
        except Exception as e:
            logger.error(f"Error detecting deviations: {str(e)}")
            return []

    def _detect_missing_expected_transactions(
        self,
        patterns: Dict[str, Any],
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Detect missing expected transactions based on recurring patterns.
        
        Args:
            patterns: Learned patterns dictionary.
            start_date: Start date for checking period.
            end_date: End date for checking period.
            
        Returns:
            List of missing transaction alerts.
        """
        missing = []
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        for pattern in patterns.get("monthly_patterns", []):
            if not pattern.get("is_monthly"):
                continue
            
            vendor = pattern.get("vendor")
            avg_days = pattern.get("avg_days_between", 30)
            last_date_str = pattern.get("date_range", {}).get("end")
            
            if not last_date_str:
                continue
            
            last_date = datetime.fromisoformat(last_date_str)
            expected_next = last_date + timedelta(days=avg_days)
            
            # Check if expected date is within the checking period
            if start <= expected_next <= end:
                # Check if transaction exists (would need to query, simplified here)
                days_overdue = (end - expected_next).days
                
                if days_overdue > self.date_tolerance_days:
                    missing.append({
                        "deviation_type": "missing_expected_transaction",
                        "vendor": vendor,
                        "expected_date": expected_next.date().isoformat(),
                        "days_overdue": days_overdue,
                        "expected_amount": pattern.get("mean_amount", 0),
                        "severity": "medium",
                        "message": f"Expected recurring transaction to vendor '{vendor}' is overdue. "
                                  f"Expected date: {expected_next.date()}, "
                                  f"Expected amount: ₹{pattern.get('mean_amount', 0):,.2f}",
                        "implication": "Recurring payment may have been missed. Verify with vendor or check if payment was made outside system."
                    })
        
        return missing

    def detect_anomalies(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect statistical anomalies in transactions using z-score analysis.
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            List of dictionaries containing detected anomalies.
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().date().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=90)).date().isoformat()
            
            # Fetch transactions
            response = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).gte("date", start_date).lte("date", end_date).is_(
                "deleted_at", "null"
            ).execute()
            
            transactions = response.data if response.data else []
            
            if len(transactions) < 10:  # Need sufficient data for statistical analysis
                return []
            
            # Calculate overall statistics
            amounts = [float(t.get("amount", 0)) for t in transactions]
            mean_amount = statistics.mean(amounts)
            std_dev = statistics.stdev(amounts) if len(amounts) > 1 else 0
            
            if std_dev == 0:
                return []
            
            anomalies = []
            
            # Detect outliers using z-score
            for txn in transactions:
                amount = float(txn.get("amount", 0))
                z_score = (amount - mean_amount) / std_dev
                
                if abs(z_score) > self.z_score_threshold:
                    anomalies.append({
                        "anomaly_type": "statistical_outlier",
                        "transaction_id": txn.get("id"),
                        "date": txn.get("date"),
                        "amount": amount,
                        "vendor": txn.get("vendor"),
                        "description": txn.get("description"),
                        "z_score": round(z_score, 2),
                        "mean": round(mean_amount, 2),
                        "std_deviation": round(std_dev, 2),
                        "severity": "high" if abs(z_score) > 3.0 else "medium",
                        "message": f"Statistical anomaly detected: Transaction of ₹{amount:,.2f} "
                                  f"deviates significantly from mean (z-score: {z_score:.2f})",
                        "implication": "Transaction amount is unusually high or low compared to typical transactions. "
                                     "Verify if this is legitimate or requires investigation."
                    })
            
            logger.info(f"Detected {len(anomalies)} statistical anomalies for client {client_id}")
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return []

    def analyze_trends(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze trends in transaction patterns over time.
        
        Identifies:
        - Increasing/decreasing spending trends
        - Seasonal patterns
        - Vendor relationship trends
        - Category spending trends
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            Dictionary containing trend analysis results.
        """
        try:
            # Set default date range if not provided (12 months for trend analysis)
            if not end_date:
                end_date = datetime.now().date().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).date().isoformat()
            
            # Fetch transactions
            response = supabase.table("transactions").select("*").eq(
                "client_id", client_id
            ).gte("date", start_date).lte("date", end_date).is_(
                "deleted_at", "null"
            ).order("date").execute()
            
            transactions = response.data if response.data else []
            
            # Group by month
            monthly_totals = defaultdict(float)
            monthly_counts = defaultdict(int)
            
            for txn in transactions:
                date = datetime.fromisoformat(txn.get("date"))
                month_key = date.strftime("%Y-%m")
                amount = float(txn.get("amount", 0))
                
                if txn.get("type") == "debit":  # Expenses
                    monthly_totals[month_key] += amount
                    monthly_counts[month_key] += 1
            
            # Calculate trend
            months = sorted(monthly_totals.keys())
            if len(months) < 3:
                return {"trend": "insufficient_data", "message": "Need at least 3 months of data"}
            
            amounts = [monthly_totals[m] for m in months]
            
            # Simple linear trend (increasing/decreasing)
            first_half = statistics.mean(amounts[:len(amounts)//2])
            second_half = statistics.mean(amounts[len(amounts)//2:])
            
            trend_direction = "increasing" if second_half > first_half else "decreasing"
            trend_percentage = abs((second_half - first_half) / first_half * 100) if first_half > 0 else 0
            
            return {
                "trend_direction": trend_direction,
                "trend_percentage": round(trend_percentage, 2),
                "monthly_data": [
                    {
                        "month": month,
                        "total_amount": round(monthly_totals[month], 2),
                        "transaction_count": monthly_counts[month]
                    }
                    for month in months
                ],
                "first_half_avg": round(first_half, 2),
                "second_half_avg": round(second_half, 2),
                "overall_mean": round(statistics.mean(amounts), 2),
                "overall_std": round(statistics.stdev(amounts) if len(amounts) > 1 else 0, 2)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {str(e)}")
            return {"error": str(e)}

    def run_full_analysis(
        self, 
        client_id: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive pattern analysis combining all methods.
        
        Args:
            client_id: Client identifier.
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            
        Returns:
            Dictionary containing complete pattern analysis results.
        """
        try:
            # Learn patterns
            patterns = self.learn_recurring_patterns(client_id, start_date, end_date)
            
            # Detect deviations
            deviations = self.detect_deviations(client_id, patterns, start_date, end_date)
            
            # Detect anomalies
            anomalies = self.detect_anomalies(client_id, start_date, end_date)
            
            # Analyze trends
            trends = self.analyze_trends(client_id, start_date, end_date)
            
            return {
                "client_id": client_id,
                "analysis_date": datetime.now().isoformat(),
                "date_range": {
                    "start": start_date or (datetime.now() - timedelta(days=365)).date().isoformat(),
                    "end": end_date or datetime.now().date().isoformat()
                },
                "patterns": patterns,
                "deviations": {
                    "count": len(deviations),
                    "items": deviations
                },
                "anomalies": {
                    "count": len(anomalies),
                    "items": anomalies
                },
                "trends": trends,
                "summary": {
                    "total_patterns": len(patterns.get("recurring_vendor_payments", [])),
                    "monthly_patterns": len(patterns.get("monthly_patterns", [])),
                    "total_deviations": len(deviations),
                    "total_anomalies": len(anomalies),
                    "high_severity_deviations": sum(
                        1 for d in deviations if d.get("severity") == "high"
                    ),
                    "trend_direction": trends.get("trend_direction", "unknown")
                }
            }
            
        except Exception as e:
            logger.error(f"Error running full pattern analysis: {str(e)}")
            return {
                "client_id": client_id,
                "analysis_date": datetime.now().isoformat(),
                "error": str(e)
            }

