from typing import List
from backend.models.compliance_models import DisallowanceResult
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger
from backend.config import settings


class IncomeTaxComplianceService:
    """
    Service for Income Tax compliance checks, including sections 40(a)(ia), 40A(3),
    business expenditure validation, and general disallowance logic.
    """

    # Cash payment limit as per Section 40A(3)
    CASH_PAYMENT_LIMIT = 10000  # ₹10,000

    # TDS threshold amounts for various sections
    TDS_THRESHOLDS = {
        "194C": 30000,  # Contractors (single transaction)
        "194J": 30000,  # Professional/technical services
        "194H": 15000,  # Commission/brokerage
        "194I": 180000,  # Rent (annual)
    }

    # Personal/non-business expense keywords
    PERSONAL_EXPENSE_KEYWORDS = [
        "personal", "family", "domestic", "household",
        "gift", "donation", "charity", "entertainment",
        "tour", "vacation", "holiday", "picnic"
    ]

    def check_40a_ia(self, transaction_ids: List[str]) -> List[DisallowanceResult]:
        """
        Perform checks for Section 40(a)(ia) disallowance on the given transactions.
        
        Section 40(a)(ia) disallows expenses where TDS was applicable but not deducted.
        
        Args:
            transaction_ids: List of transaction IDs to evaluate.
        
        Returns:
            List of DisallowanceResult objects indicating any disallowances found.
        """
        results = []
        
        if not transaction_ids:
            return results
        
        try:
            # TODO: Fetch transactions and apply 40(a)(ia) rules
            # Fetch transactions from database
            response = supabase.table("transactions").select("*").in_("id", transaction_ids).execute()
            transactions = response.data if response.data else []
            
            for txn in transactions:
                txn_id = txn.get("id", "")
                amount = float(txn.get("amount", 0))
                description = str(txn.get("description", "")).lower()
                ledger = str(txn.get("ledger", "")).lower()
                tds_applicable = txn.get("tds_applicable", False)
                tds_deducted = txn.get("tds_deducted", False)
                
                # Check if TDS was applicable but not deducted
                if tds_applicable and not tds_deducted:
                    # Determine the applicable TDS section based on description/ledger
                    tds_section = self._determine_tds_section(description, ledger)
                    
                    results.append(DisallowanceResult(
                        transaction_id=txn_id,
                        section="40(a)(ia)",
                        reason=f"TDS not deducted on payment of ₹{amount:,.2f}. Applicable section: {tds_section}"
                    ))
                
                # Additional check: High-value payments that should have TDS
                elif not tds_applicable and amount > 30000:
                    # Check if this is a payment type that requires TDS
                    if any(keyword in description or keyword in ledger for keyword in ["professional", "consultant", "contractor", "commission", "rent"]):
                        results.append(DisallowanceResult(
                            transaction_id=txn_id,
                            section="40(a)(ia)",
                            reason=f"Potential TDS requirement not marked for payment of ₹{amount:,.2f}"
                        ))
            
            logger.info(f"Section 40(a)(ia) check completed: {len(results)} issues found")
            
        except Exception as e:
            logger.error(f"Section 40(a)(ia) check failed: {e}")
        
        return results

    def check_40A_3_cash_limits(self, transaction_ids: List[str]) -> List[DisallowanceResult]:
        """
        Enforce cash transaction limits as per Section 40A(3).
        
        Section 40A(3) disallows cash payments exceeding ₹10,000 in a single day to a single party.
        
        Args:
            transaction_ids: List of transaction IDs to evaluate.
        
        Returns:
            List of DisallowanceResult objects for transactions exceeding cash limits.
        """
        results = []
        
        if not transaction_ids:
            return results
        
        try:
            # TODO: Fetch transactions and apply cash limit thresholds
            # Fetch transactions from database
            response = supabase.table("transactions").select("*").in_("id", transaction_ids).execute()
            transactions = response.data if response.data else []
            
            for txn in transactions:
                txn_id = txn.get("id", "")
                amount = float(txn.get("amount", 0))
                payment_mode = str(txn.get("mode", "")).upper() if txn.get("mode") else ""
                vendor = txn.get("vendor", "Unknown")
                
                # Check if payment is in cash and exceeds limit
                if payment_mode == "CASH" and amount > self.CASH_PAYMENT_LIMIT:
                    results.append(DisallowanceResult(
                        transaction_id=txn_id,
                        section="40A(3)",
                        reason=f"Cash payment of ₹{amount:,.2f} to {vendor} exceeds limit of ₹{self.CASH_PAYMENT_LIMIT:,.0f}"
                    ))
            
            logger.info(f"Section 40A(3) check completed: {len(results)} issues found")
            
        except Exception as e:
            logger.error(f"Section 40A(3) check failed: {e}")
        
        return results

    def validate_business_expenditure(self, transaction_ids: List[str]) -> List[DisallowanceResult]:
        """
        Validate that business expenditures are allowable under Income Tax rules.
        
        Checks for personal expenses, capital expenditures, and non-business related costs.
        
        Args:
            transaction_ids: List of transaction IDs to evaluate.
        
        Returns:
            List of DisallowanceResult objects for non‑allowable expenditures.
        """
        results = []
        
        if not transaction_ids:
            return results
        
        try:
            # TODO: Apply business expenditure validation logic
            # Fetch transactions from database
            response = supabase.table("transactions").select("*").in_("id", transaction_ids).execute()
            transactions = response.data if response.data else []
            
            for txn in transactions:
                txn_id = txn.get("id", "")
                amount = float(txn.get("amount", 0))
                description = str(txn.get("description", "")).lower()
                ledger = str(txn.get("ledger", "")).lower()
                capital_expense = txn.get("capital_expense", False)
                
                # Check 1: Personal expenses (Section 37)
                for personal_keyword in self.PERSONAL_EXPENSE_KEYWORDS:
                    if personal_keyword in description or personal_keyword in ledger:
                        results.append(DisallowanceResult(
                            transaction_id=txn_id,
                            section="37(1)",
                            reason=f"Potential personal expense ('{personal_keyword}') of ₹{amount:,.2f} - not wholly and exclusively for business"
                        ))
                        break
                
                # Check 2: Capital expenditure incorrectly claimed as revenue
                # Capital expenses should be depreciated, not claimed as expense
                if capital_expense:
                    results.append(DisallowanceResult(
                        transaction_id=txn_id,
                        section="37(1)",
                        reason=f"Capital expenditure of ₹{amount:,.2f} cannot be claimed as revenue expense. Should be depreciated."
                    ))
                
                # Check 3: Excessive or unreasonable expenses (Section 40A(2))
                # Flag very high amounts for review
                if amount > 1000000:  # ₹10 Lakhs
                    results.append(DisallowanceResult(
                        transaction_id=txn_id,
                        section="40A(2)",
                        reason=f"High-value expense of ₹{amount:,.2f} - verify if reasonable and for business purposes"
                    ))
            
            logger.info(f"Business expenditure validation completed: {len(results)} issues found")
            
        except Exception as e:
            logger.error(f"Business expenditure validation failed: {e}")
        
        return results

    def evaluate_disallowance(self, transaction_ids: List[str]) -> List[DisallowanceResult]:
        """
        General disallowance evaluation that aggregates all applicable Income Tax rules.
        
        This method combines checks from all specific sections to provide a comprehensive
        disallowance report.
        
        Args:
            transaction_ids: List of transaction IDs to evaluate.
        
        Returns:
            List of DisallowanceResult objects summarizing all disallowance findings.
        """
        all_results = []
        
        if not transaction_ids:
            return all_results
        
        try:
            # TODO: Combine results from specific checks or apply generic rules
            # Run all specific compliance checks
            
            # Check 1: Section 40(a)(ia) - TDS non-deduction
            tds_results = self.check_40a_ia(transaction_ids)
            all_results.extend(tds_results)
            
            # Check 2: Section 40A(3) - Cash payment limits
            cash_results = self.check_40A_3_cash_limits(transaction_ids)
            all_results.extend(cash_results)
            
            # Check 3: Business expenditure validation
            business_exp_results = self.validate_business_expenditure(transaction_ids)
            all_results.extend(business_exp_results)
            
            # Remove duplicates (same transaction_id and section)
            unique_results = []
            seen = set()
            
            for result in all_results:
                key = (result.transaction_id, result.section)
                if key not in seen:
                    seen.add(key)
                    unique_results.append(result)
            
            logger.info(f"Comprehensive disallowance evaluation completed: {len(unique_results)} unique issues found")
            
            return unique_results
            
        except Exception as e:
            logger.error(f"Disallowance evaluation failed: {e}")
            return []

    def _determine_tds_section(self, description: str, ledger: str) -> str:
        """
        Helper method to determine applicable TDS section based on transaction description.
        
        Args:
            description: Transaction description
            ledger: Ledger/category
            
        Returns:
            Applicable TDS section code
        """
        # Check for contractor payments (194C)
        if any(keyword in description or keyword in ledger for keyword in ["contractor", "contract", "construction", "labour"]):
            return "194C"
        
        # Check for professional/technical services (194J)
        if any(keyword in description or keyword in ledger for keyword in ["professional", "consultant", "technical", "legal", "ca", "architect"]):
            return "194J"
        
        # Check for commission/brokerage (194H)
        if any(keyword in description or keyword in ledger for keyword in ["commission", "brokerage", "agent"]):
            return "194H"
        
        # Check for rent (194I)
        if any(keyword in description or keyword in ledger for keyword in ["rent", "lease"]):
            return "194I"
        
        # Default
        return "Applicable TDS Section"
