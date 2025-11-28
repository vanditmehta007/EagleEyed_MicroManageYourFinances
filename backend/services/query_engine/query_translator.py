# backend/services/query_engine/query_translator.py

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re
from backend.utils.logger import logger


class QueryTranslator:
    """
    Translates natural language queries into structured components for database execution.
    
    Converts queries like:
    - "Show all expenses above 50,000 in Q2 2024"
    - "List rent payments to ABC Landlords"
    - "What are my GST liabilities this month?"
    
    Into structured filters, SQL fragments, entity maps, and retrieval parameters.
    
    This is a rule-based translator that can work standalone or be enhanced with LLM parsing.
    """

    def __init__(self) -> None:
        # TODO: Initialize keyword dictionaries and regex patterns
        self._init_keyword_maps()
        logger.info("QueryTranslator initialized")

    def translate(self, query_text: str) -> Dict[str, Any]:
        """
        Main translation method that converts NL query to structured components.
        """
        # TODO: Normalize query text
        normalized = query_text.lower().strip()
        
        # TODO: Extract intent using self._extract_intent
        intent = self._extract_intent(normalized)
        
        # TODO: Extract entity type using self._extract_entity_type
        entity_type = self._extract_entity_type(normalized)
        
        # TODO: Extract filters using self._extract_filters
        filters = self._extract_filters(normalized)
        
        # TODO: Generate SQL fragments using self._generate_sql_fragments
        sql_fragments = self._generate_sql_fragments(filters)
        
        # TODO: Build entity map using self._build_entity_map
        entity_map = self._build_entity_map(normalized)
        
        # TODO: Create retrieval params using self._create_retrieval_params
        retrieval_params = self._create_retrieval_params(normalized, filters)
        
        # TODO: Return complete translation dict
        result = {
            "intent": intent,
            "entity_type": entity_type,
            "filters": filters,
            "sql_fragments": sql_fragments,
            "entity_map": entity_map,
            "retrieval_params": retrieval_params
        }
        
        logger.info(f"Translated query: intent={intent}, entity={entity_type}, filters={len(filters)}")
        return result

    def _init_keyword_maps(self) -> None:
        """
        Initialize keyword dictionaries for pattern matching.
        """
        # TODO: Define intent keywords
        self.intent_keywords = {
            "list": ["show", "list", "display", "get", "find", "view"],
            "filter": ["where", "with", "having", "above", "below", "between"],
            "aggregate": ["total", "sum", "count", "average", "how many", "how much"],
            "compliance_check": ["gst", "tds", "tax", "compliance", "liability", "applicable"]
        }
        
        # TODO: Define entity type keywords
        self.entity_keywords = {
            "transaction": ["expense", "payment", "transaction", "entry", "debit", "credit"],
            "client": ["client", "customer", "company"],
            "sheet": ["sheet", "book", "ledger", "account"],
            "document": ["document", "invoice", "bill", "receipt"]
        }
        
        # TODO: Define ledger keywords
        self.ledger_keywords = {
            "Rent": ["rent", "rental", "lease"],
            "Salaries": ["salary", "wages", "payroll", "compensation"],
            "Travel Expenses": ["travel", "trip", "flight", "hotel"],
            "Utilities": ["electricity", "water", "utility", "utilities"],
            "Professional Fees": ["professional", "consultant", "legal", "audit"]
        }
        
        # TODO: Define time period keywords
        self.time_keywords = {
            "today": 0,
            "yesterday": 1,
            "this week": 7,
            "this month": 30,
            "this quarter": 90,
            "this year": 365
        }

    def _extract_intent(self, query_text: str) -> str:
        """
        Extract the primary intent from the query.
        """
        # TODO: Check for intent keywords in query
        for intent, keywords in self.intent_keywords.items():
            if any(kw in query_text for kw in keywords):
                return intent
        
        # TODO: Return matched intent or default to "list"
        return "list"

    def _extract_entity_type(self, query_text: str) -> str:
        """
        Determine the primary entity type being queried.
        """
        # TODO: Check for entity keywords in query
        for entity, keywords in self.entity_keywords.items():
            if any(kw in query_text for kw in keywords):
                return entity
        
        # TODO: Return matched entity type or default to "transaction"
        return "transaction"

    def _extract_filters(self, query_text: str) -> Dict[str, Any]:
        """
        Extract filter conditions from the query.
        """
        filters = {}
        
        # TODO: Extract ledger filter using self._extract_ledger
        ledger = self._extract_ledger(query_text)
        if ledger:
            filters["ledger"] = ledger
        
        # TODO: Extract date range using self._extract_date_range
        date_range = self._extract_date_range(query_text)
        if date_range.get("date_from"):
            filters["date_from"] = date_range["date_from"]
        if date_range.get("date_to"):
            filters["date_to"] = date_range["date_to"]
        
        # TODO: Extract amount range using self._extract_amount_range
        amount_range = self._extract_amount_range(query_text)
        if amount_range.get("amount_min") is not None:
            filters["amount_min"] = amount_range["amount_min"]
        if amount_range.get("amount_max") is not None:
            filters["amount_max"] = amount_range["amount_max"]
        
        # TODO: Extract vendor using self._extract_vendor
        vendor = self._extract_vendor(query_text)
        if vendor:
            filters["vendor"] = vendor
        
        # TODO: Extract transaction type (credit/debit) using self._extract_transaction_type
        txn_type = self._extract_transaction_type(query_text)
        if txn_type:
            filters["transaction_type"] = txn_type
        
        return filters

    def _extract_ledger(self, query_text: str) -> Optional[str]:
        """
        Extract ledger account name from query.
        """
        # TODO: Check for ledger keywords
        for ledger, keywords in self.ledger_keywords.items():
            if any(kw in query_text for kw in keywords):
                return ledger
        
        # TODO: Return matched ledger or None
        return None

    def _extract_date_range(self, query_text: str) -> Dict[str, Optional[str]]:
        """
        Extract date range from query.
        """
        # TODO: Check for time period keywords (this month, Q2 2024, etc.)
        today = datetime.utcnow()
        
        for period, days in self.time_keywords.items():
            if period in query_text:
                date_from = (today - timedelta(days=days)).strftime("%Y-%m-%d")
                date_to = today.strftime("%Y-%m-%d")
                return {"date_from": date_from, "date_to": date_to}
        
        # TODO: Check for explicit dates (2024-01-15, Jan 15 2024, etc.)
        # Check for year patterns (2024, 2023, etc.)
        year_match = re.search(r'\b(20\d{2})\b', query_text)
        if year_match:
            year = year_match.group(1)
            
            # Check for quarter (Q1, Q2, Q3, Q4)
            quarter_match = re.search(r'q([1-4])', query_text)
            if quarter_match:
                q = int(quarter_match.group(1))
                month_start = (q - 1) * 3 + 1
                month_end = q * 3
                return {
                    "date_from": f"{year}-{month_start:02d}-01",
                    "date_to": f"{year}-{month_end:02d}-{self._last_day_of_month(int(year), month_end):02d}"
                }
            
            # Just year
            return {"date_from": f"{year}-01-01", "date_to": f"{year}-12-31"}
        
        # TODO: Calculate date range
        # TODO: Return dict with date_from and date_to
        return {"date_from": None, "date_to": None}

    def _extract_amount_range(self, query_text: str) -> Dict[str, Optional[float]]:
        """
        Extract amount range from query.
        """
        # TODO: Use regex to find numbers with keywords like "above", "below", "between"
        amount_min = None
        amount_max = None
        
        # Above/greater than pattern
        above_match = re.search(r'(?:above|greater than|more than|over)\s+([\d,]+)', query_text)
        if above_match:
            amount_min = float(above_match.group(1).replace(',', ''))
        
        # Below/less than pattern
        below_match = re.search(r'(?:below|less than|under)\s+([\d,]+)', query_text)
        if below_match:
            amount_max = float(below_match.group(1).replace(',', ''))
        
        # Between pattern
        between_match = re.search(r'between\s+([\d,]+)\s+and\s+([\d,]+)', query_text)
        if between_match:
            amount_min = float(between_match.group(1).replace(',', ''))
            amount_max = float(between_match.group(2).replace(',', ''))
        
        # TODO: Parse amount values
        # TODO: Return dict with amount_min and amount_max
        return {"amount_min": amount_min, "amount_max": amount_max}

    def _extract_vendor(self, query_text: str) -> Optional[str]:
        """
        Extract vendor name from query.
        """
        # TODO: Look for patterns like "to [vendor]", "from [vendor]", "vendor [name]"
        patterns = [
            r'to\s+([A-Z][A-Za-z\s]+?)(?:\s|$)',
            r'from\s+([A-Z][A-Za-z\s]+?)(?:\s|$)',
            r'vendor\s+([A-Z][A-Za-z\s]+?)(?:\s|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_text, re.IGNORECASE)
            if match:
                vendor = match.group(1).strip()
                # TODO: Extract vendor name
                # TODO: Return vendor or None
                return vendor
        
        return None

    def _extract_transaction_type(self, query_text: str) -> Optional[str]:
        """
        Extract transaction type (credit/debit) from query.
        """
        # TODO: Check for keywords like "expense", "payment" (debit) or "income", "receipt" (credit)
        debit_keywords = ["expense", "payment", "paid", "debit", "purchase"]
        credit_keywords = ["income", "receipt", "received", "credit", "revenue"]
        
        if any(kw in query_text for kw in debit_keywords):
            return "debit"
        elif any(kw in query_text for kw in credit_keywords):
            return "credit"
        
        # TODO: Return transaction type or None
        return None

    def _generate_sql_fragments(self, filters: Dict[str, Any]) -> List[str]:
        """
        Generate SQL WHERE clause fragments from filters.
        """
        # TODO: Convert filters to SQL fragments
        fragments = []
        
        if "ledger" in filters:
            fragments.append(f"ledger = '{filters['ledger']}'")
        
        if "date_from" in filters:
            fragments.append(f"date >= '{filters['date_from']}'")
        
        if "date_to" in filters:
            fragments.append(f"date <= '{filters['date_to']}'")
        
        if "amount_min" in filters:
            fragments.append(f"amount >= {filters['amount_min']}")
        
        if "amount_max" in filters:
            fragments.append(f"amount <= {filters['amount_max']}")
        
        if "vendor" in filters:
            fragments.append(f"vendor ILIKE '%{filters['vendor']}%'")
        
        if "transaction_type" in filters:
            fragments.append(f"transaction_type = '{filters['transaction_type']}'")
        
        # TODO: Handle date ranges, amount ranges, string matching
        # TODO: Return list of SQL fragments
        return fragments

    def _build_entity_map(self, query_text: str) -> Dict[str, str]:
        """
        Build a map of entities mentioned in the query.
        """
        # TODO: Extract named entities (vendors, clients, ledgers)
        entity_map = {}
        
        ledger = self._extract_ledger(query_text)
        if ledger:
            entity_map["ledger"] = ledger
        
        vendor = self._extract_vendor(query_text)
        if vendor:
            entity_map["vendor"] = vendor
        
        # TODO: Return entity map
        return entity_map

    def _create_retrieval_params(self, query_text: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create parameters for RAG retrieval based on query context.
        """
        # TODO: Determine retrieval strategy based on query type
        params = {
            "top_k": 5,
            "metadata_filters": {},
            "query_text": query_text
        }
        
        # TODO: Set top_k based on query complexity
        if "compliance" in query_text or "gst" in query_text or "tds" in query_text:
            params["top_k"] = 10  # More context for compliance queries
        
        # TODO: Add metadata filters for RAG
        if "ledger" in filters:
            params["metadata_filters"]["ledger"] = filters["ledger"]
        
        # TODO: Return retrieval params
        return params

    def _last_day_of_month(self, year: int, month: int) -> int:
        """Helper to get last day of month."""
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        last_day = next_month - timedelta(days=1)
        return last_day.day
