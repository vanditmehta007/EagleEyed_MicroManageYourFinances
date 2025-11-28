# backend/services/ledger_classifier/ledger_rules_engine.py

from typing import Dict, Any, Optional
import re

class LedgerRulesEngine:
    """
    Rule-based classification engine for ledger accounts.
    
    Provides deterministic heuristics for:
    - Ledger account classification based on keywords and patterns
    - GST applicability indicators
    - TDS applicability indicators
    - Capital vs Revenue expense classification
    - Recurring transaction detection
    
    This engine complements AI-based classification with explicit business rules.
    """

    def __init__(self) -> None:
        # Define keyword-to-ledger mapping rules
        self.ledger_rules = {
            "Rent Expense": ["rent", "lease", "rental"],
            "Salary & Wages": ["salary", "wages", "payroll", "employee", "staff"],
            "Professional Fees": ["consultant", "legal", "audit", "ca fees", "professional"],
            "Electricity Expense": ["electricity", "power", "eb bill", "mseb"],
            "Telephone Expense": ["telephone", "mobile", "airtel", "jio", "vodafone"],
            "Internet Expense": ["internet", "broadband", "wifi"],
            "Office Supplies": ["stationery", "office supplies", "printing"],
            "Travel Expense": ["travel", "flight", "train", "taxi", "uber", "ola"],
            "Fuel Expense": ["petrol", "diesel", "fuel", "cng"],
            "Repairs & Maintenance": ["repair", "maintenance", "servicing"],
            "Insurance Expense": ["insurance", "premium", "policy"],
            "Bank Charges": ["bank charges", "bank fee", "service charge"],
            "Interest Expense": ["interest", "loan interest", "emi"],
            "Depreciation": ["depreciation"],
            "Purchase of Goods": ["purchase", "inventory", "stock"],
            "Sales": ["sales", "revenue", "income"],
            "Fixed Assets": ["machinery", "equipment", "vehicle", "computer", "furniture", "building"]
        }
        
        # GST blocked credit categories (Section 17(5))
        self.gst_blocked_keywords = ["food", "beverage", "restaurant", "hotel", "guest house", "club"]
        
        # TDS applicable categories with thresholds
        self.tds_categories = {
            "194C": {"keywords": ["contractor", "contract", "labour"], "threshold": 30000},
            "194J": {"keywords": ["professional", "consultant", "technical", "legal", "audit"], "threshold": 30000},
            "194I": {"keywords": ["rent"], "threshold": 240000},
            "194H": {"keywords": ["commission", "brokerage"], "threshold": 15000}
        }
        
        # Capital expense keywords
        self.capital_keywords = ["machinery", "equipment", "vehicle", "computer", "furniture", "building", "land", "plant"]
        
        # Recurring expense keywords
        self.recurring_keywords = ["rent", "salary", "subscription", "insurance", "emi", "lease"]

    def classify_by_rules(self, transaction: Dict[str, Any]) -> Optional[str]:
        """
        Classify a transaction into a ledger account using rule-based logic.
        """
        description = str(transaction.get("description", "")).lower()
        
        # Normalize description
        description = re.sub(r'[^a-z0-9\s]', '', description)
        
        # Check each ledger rule
        for ledger, keywords in self.ledger_rules.items():
            for keyword in keywords:
                if keyword in description:
                    return ledger
        
        return None

    def is_gst_applicable(self, transaction: Dict[str, Any]) -> bool:
        """
        Determine if GST is applicable for a transaction.
        """
        description = str(transaction.get("description", "")).lower()
        gstin = transaction.get("gstin")
        
        # Check for blocked credit categories
        for blocked_keyword in self.gst_blocked_keywords:
            if blocked_keyword in description:
                return False
        
        # GST is generally applicable if vendor has GSTIN
        if gstin and len(gstin) == 15:
            return True
        
        # Default: assume GST applicable for purchases
        txn_type = transaction.get("type", "").lower()
        if txn_type in ["debit", "expense", "purchase"]:
            return True
        
        return False

    def is_tds_applicable(self, transaction: Dict[str, Any]) -> bool:
        """
        Determine if TDS is applicable for a transaction.
        """
        description = str(transaction.get("description", "")).lower()
        amount = float(transaction.get("amount", 0))
        
        # Check each TDS category
        for section, config in self.tds_categories.items():
            # Check if keywords match
            keyword_match = any(kw in description for kw in config["keywords"])
            
            # Check if amount exceeds threshold
            threshold_met = amount >= config["threshold"]
            
            if keyword_match and threshold_met:
                return True
        
        return False

    def is_capital_expense(self, transaction: Dict[str, Any]) -> bool:
        """
        Determine if a transaction is a capital expense vs revenue expense.
        """
        description = str(transaction.get("description", "")).lower()
        amount = float(transaction.get("amount", 0))
        
        # Check for capital asset keywords
        for keyword in self.capital_keywords:
            if keyword in description:
                return True
        
        # High-value purchases (> 50,000) are likely capital
        if amount > 50000:
            return True
        
        return False

    def is_recurring(self, transaction: Dict[str, Any]) -> bool:
        """
        Determine if a transaction is recurring (e.g., rent, salary, subscription).
        """
        description = str(transaction.get("description", "")).lower()
        
        # Check for recurring keywords
        for keyword in self.recurring_keywords:
            if keyword in description:
                return True
        
        # TODO: Implement historical pattern matching (same vendor, similar amount, regular frequency)
        # This would require querying past transactions
        
        return False

    def get_confidence_score(self, transaction: Dict[str, Any], ledger: str) -> float:
        """
        Calculate a confidence score for a rule-based classification.
        """
        description = str(transaction.get("description", "")).lower()
        
        if not ledger or ledger not in self.ledger_rules:
            return 0.5  # Default medium confidence for unknown ledgers
        
        # Count how many keywords from the ledger match
        keywords = self.ledger_rules[ledger]
        matches = sum(1 for kw in keywords if kw in description)
        
        # Base confidence based on number of matches
        if matches >= 2:
            return 0.95  # High confidence if multiple keywords match
        elif matches == 1:
            return 0.75  # Medium-high confidence for single match
        else:
            return 0.5   # Medium confidence if no direct match
