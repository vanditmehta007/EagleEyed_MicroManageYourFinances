from typing import List, Dict, Any, Optional
from backend.models.compliance_models import TDSCheckResult
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger

class TDSEngine:
    """
    Service for TDS (Tax Deducted at Source) compliance checks.
    
    Implements threshold checks and section detection for:
    - Section 194C: Payments to contractors
    - Section 194J: Professional/technical services
    - Section 194I: Rent payments
    - Section 194H: Commission/brokerage
    - Section 194A: Interest payments
    """

    def __init__(self):
        # Define TDS sections with thresholds and keywords
        self.tds_sections = {
            "194C": {
                "name": "Payments to Contractors",
                "threshold_single": 30000,
                "threshold_aggregate": 100000,
                "rate": 1.0,  # 1% for individuals, 2% for others
                "keywords": ["contractor", "contract", "sub-contract", "labour", "work order", "construction"]
            },
            "194J": {
                "name": "Professional/Technical Services",
                "threshold_single": 30000,
                "threshold_aggregate": 30000,
                "rate": 10.0,
                "keywords": ["professional", "consultant", "consulting", "technical", "legal", "audit", "ca", "architect", "engineer", "advisory"]
            },
            "194I": {
                "name": "Rent Payments",
                "threshold_single": 240000,  # Annual threshold
                "threshold_aggregate": 240000,
                "rate": 10.0,  # 10% for land/building, 2% for plant/machinery
                "keywords": ["rent", "lease", "rental", "tenancy"]
            },
            "194H": {
                "name": "Commission/Brokerage",
                "threshold_single": 15000,
                "threshold_aggregate": 15000,
                "rate": 5.0,
                "keywords": ["commission", "brokerage", "broker", "agent", "incentive"]
            },
            "194A": {
                "name": "Interest Payments",
                "threshold_single": 40000,  # For individuals, 50000 for others
                "threshold_aggregate": 40000,
                "rate": 10.0,
                "keywords": ["interest", "loan interest", "deposit interest"]
            }
        }

    def check_tds(self, transaction_ids: List[str]) -> List[TDSCheckResult]:
        """
        Determine TDS applicability for a list of transactions.
        """
        results = []
        
        if not transaction_ids:
            return results
        
        try:
            # Fetch transactions from database
            response = supabase.table("transactions").select("*").in_("id", transaction_ids).execute()
            transactions = response.data if response.data else []
            
            for txn in transactions:
                result = self._check_transaction_tds(txn)
                results.append(result)
            
        except Exception as e:
            logger.error(f"TDS check failed: {e}")
        
        return results

    def _check_transaction_tds(self, txn: Dict[str, Any]) -> TDSCheckResult:
        """
        Check TDS applicability for a single transaction.
        """
        amount = float(txn.get("amount", 0))
        description = str(txn.get("description", "")).lower()
        ledger = str(txn.get("ledger", "")).lower()
        
        tds_applicable = False
        section = None
        threshold = None
        reason = None
        
        # Check each TDS section
        for sec_code, sec_data in self.tds_sections.items():
            # Check if keywords match
            keyword_match = any(
                kw in description or kw in ledger 
                for kw in sec_data["keywords"]
            )
            
            if keyword_match:
                # Check if amount exceeds threshold
                if amount >= sec_data["threshold_single"]:
                    tds_applicable = True
                    section = sec_code
                    threshold = sec_data["threshold_single"]
                    reason = f"{sec_data['name']} exceeding threshold of ₹{threshold:,.0f} (Rate: {sec_data['rate']}%)"
                    break  # Use first matching section
        
        return TDSCheckResult(
            transaction_id=txn.get("id", ""),
            tds_applicable=tds_applicable,
            section=section,
            threshold=threshold,
            reason=reason
        )

    def evaluate_threshold(self, amount: float, transaction_type: str) -> bool:
        """
        Evaluate whether the transaction amount exceeds the TDS threshold for its type.
        """
        if transaction_type in self.tds_sections:
            threshold = self.tds_sections[transaction_type]["threshold_single"]
            return amount >= threshold
        
        return False

    def detect_section(self, description: str) -> Optional[str]:
        """
        Detect the relevant Income Tax Act section for TDS based on transaction description.
        """
        description_lower = description.lower()
        
        for sec_code, sec_data in self.tds_sections.items():
            if any(kw in description_lower for kw in sec_data["keywords"]):
                return sec_code
        
        return None

    def get_compliance_notes(self, transaction_id: str) -> str:
        """
        Retrieve compliance notes or remarks for a specific transaction's TDS assessment.
        """
        try:
            # Fetch transaction
            response = supabase.table("transactions").select("*").eq("id", transaction_id).execute()
            
            if not response.data:
                return "Transaction not found"
            
            txn = response.data[0]
            result = self._check_transaction_tds(txn)
            
            if result.tds_applicable:
                return f"TDS applicable under Section {result.section}. {result.reason}. Ensure TDS is deducted and deposited within due date."
            else:
                return "TDS not applicable for this transaction based on current thresholds and description."
        
        except Exception as e:
            logger.error(f"Failed to get compliance notes: {e}")
            return "Error retrieving compliance notes"

    def calculate_tds_amount(self, amount: float, section: str) -> float:
        """
        Calculate TDS amount based on section and amount.
        """
        if section in self.tds_sections:
            rate = self.tds_sections[section]["rate"]
            return round(amount * rate / 100, 2)
        
        return 0.0
