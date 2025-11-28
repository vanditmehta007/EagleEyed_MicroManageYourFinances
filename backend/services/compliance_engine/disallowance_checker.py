from typing import List
from backend.models.compliance_models import DisallowanceResult
from backend.utils.supabase_client import supabase
from backend.config import settings

class DisallowanceChecker:
    """
    Service for identifying potentially disallowable expenses under the Income Tax Act
    based on transaction patterns and vendor attributes.
    """

    def check_disallowances(self, transaction_ids: List[str]) -> List[DisallowanceResult]:
        """
        Identify potentially disallowable expenses for a list of transaction IDs.

        Args:
            transaction_ids: List of transaction identifiers to evaluate.

        Returns:
            List of DisallowanceResult objects describing any disallowances found.
        """
        results = []
        
        if not transaction_ids:
            return results
        
        try:
            # Fetch transactions from database
            response = supabase.table("transactions").select("*").in_("id", transaction_ids).execute()
            transactions = response.data if response.data else []
            
            for txn in transactions:
                amount = float(txn.get("amount", 0))
                mode = txn.get("mode", "").upper() if txn.get("mode") else ""
                gstin = txn.get("gstin")
                vendor = txn.get("vendor")
                
                # Section 40A(3) - Cash payments above ₹10,000
                if mode == "CASH" and amount > settings.CASH_PAYMENT_LIMIT:
                    results.append(DisallowanceResult(
                        transaction_id=txn.get("id", ""),
                        section="40A(3)",
                        reason=f"Cash payment of ₹{amount:,.2f} exceeds limit of ₹{settings.CASH_PAYMENT_LIMIT:,.0f}"
                    ))
                
                # Section 40(a)(ia) - Payments without TDS deduction
                # Check if TDS was applicable but not deducted
                if txn.get("tds_applicable") and not txn.get("tds_deducted"):
                    results.append(DisallowanceResult(
                        transaction_id=txn.get("id", ""),
                        section="40(a)(ia)",
                        reason="TDS applicable but not deducted on payment"
                    ))
                
                # Section 40A(2) - Excessive payments to related parties
                # This would require vendor relationship data - placeholder for now
                
                # Missing GSTIN for registered vendors
                if vendor and not gstin and amount > 0:
                    # Check if vendor should be registered (heuristic: large amounts)
                    if amount > 200000:  # Threshold for GST registration
                        results.append(DisallowanceResult(
                            transaction_id=txn.get("id", ""),
                            section="General",
                            reason=f"Missing GSTIN for vendor '{vendor}' on transaction of ₹{amount:,.2f}"
                        ))
            
        except Exception as e:
            # Return empty results on error
            pass
        
        return results

    def evaluate_vendor_risk(self, vendor_id: str) -> float:
        """
        Evaluate a risk score for a vendor that may influence disallowance decisions.

        Args:
            vendor_id: Identifier of the vendor to assess.

        Returns:
            A numeric risk score (higher indicates greater likelihood of disallowance).
            Score ranges from 0 (low risk) to 100 (high risk).
        """
        risk_score = 0.0
        
        try:
            # TODO: Retrieve vendor metadata (e.g., registration status, past compliance flags)
            # Fetch all transactions for this vendor to analyze patterns
            # Note: vendor_id in this context is the vendor name from transactions
            transactions_response = supabase.table("transactions").select("*").eq("vendor", vendor_id).is_("deleted_at", "null").execute()
            
            if not transactions_response.data:
                # No transaction history - moderate risk
                return 50.0
            
            transactions = transactions_response.data
            transaction_count = len(transactions)
            
            # TODO: Compute a risk score based on predefined criteria
            # Risk factors to consider:
            
            # 1. Missing GSTIN/PAN (20 points)
            missing_gstin_count = sum(1 for txn in transactions if not txn.get("gstin"))
            missing_pan_count = sum(1 for txn in transactions if not txn.get("pan"))
            
            if missing_gstin_count > 0:
                # Percentage of transactions without GSTIN
                gstin_missing_ratio = missing_gstin_count / transaction_count
                risk_score += gstin_missing_ratio * 20
            
            if missing_pan_count > 0:
                # Percentage of transactions without PAN
                pan_missing_ratio = missing_pan_count / transaction_count
                risk_score += pan_missing_ratio * 15
            
            # 2. High-value cash transactions (25 points)
            cash_transactions = [
                txn for txn in transactions 
                if txn.get("mode", "").upper() == "CASH"
            ]
            
            if cash_transactions:
                cash_ratio = len(cash_transactions) / transaction_count
                risk_score += cash_ratio * 25
                
                # Additional risk for high-value cash transactions
                high_value_cash = sum(
                    1 for txn in cash_transactions 
                    if float(txn.get("amount", 0)) > 10000
                )
                if high_value_cash > 0:
                    risk_score += min(high_value_cash * 5, 15)  # Cap at 15 points
            
            # 3. TDS non-compliance (20 points)
            tds_issues = sum(
                1 for txn in transactions 
                if txn.get("tds_applicable") and not txn.get("tds_deducted")
            )
            
            if tds_issues > 0:
                tds_issue_ratio = tds_issues / transaction_count
                risk_score += tds_issue_ratio * 20
            
            # 4. Transaction amount patterns (15 points)
            total_amount = sum(float(txn.get("amount", 0)) for txn in transactions)
            avg_amount = total_amount / transaction_count if transaction_count > 0 else 0
            
            # High average transaction amounts increase risk
            if avg_amount > 500000:  # ₹5 Lakhs
                risk_score += 15
            elif avg_amount > 200000:  # ₹2 Lakhs
                risk_score += 10
            elif avg_amount > 100000:  # ₹1 Lakh
                risk_score += 5
            
            # 5. Frequency and consistency (5 points)
            # Very few transactions with vendor might indicate one-off/suspicious activity
            if transaction_count == 1:
                risk_score += 5
            elif transaction_count == 2:
                risk_score += 3
            
            # Cap the risk score at 100
            risk_score = min(risk_score, 100.0)
            
            # Round to 2 decimal places
            risk_score = round(risk_score, 2)
            
        except Exception as e:
            # On error, return moderate risk score
            risk_score = 50.0
        
        return risk_score
