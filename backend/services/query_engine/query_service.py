# backend/services/query_engine/query_service.py

from typing import Dict, Any, List, Optional
import re
from datetime import datetime
from backend.models.query_models import QueryRequest, QueryResult
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger
from backend.services.rag_service.embedding_service import EmbeddingService

class QueryService:
    """
    High-level orchestrator for natural language query processing.
    """

    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        
        self.ledger_keywords = {
            "rent": "Rent Expense",
            "salary": "Salary & Wages",
            "professional": "Professional Fees",
            "electricity": "Electricity Expense",
            "travel": "Travel Expense",
            "fuel": "Fuel Expense",
            "insurance": "Insurance Expense"
        }
        
        self.intent_patterns = {
            "list": ["show", "list", "display", "get", "find"],
            "aggregate": ["total", "sum", "count", "average"],
            "compliance": ["gst", "tds", "tax", "compliance", "law"]
        }

    def process_query(self, request: QueryRequest) -> QueryResult:
        """
        Execute a natural language query on financial data.
        """
        try:
            query_text = request.query.lower()
            explicit_filters = request.filters or {}
            
            parsed = self._parse_query(query_text)
            filters = self._extract_filters(parsed, explicit_filters)
            
            db_query = self._build_db_query(filters, parsed)
            result_data = self._execute_query(db_query)
            
            law_references = []
            if parsed.get("intent") == "compliance":
                law_references = self._get_rag_context(query_text)
            
            return self._assemble_response(result_data, law_references, query_text, parsed)
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return QueryResult(
                table=[],
                summary=f"Error processing query: {str(e)}",
                law_references=None
            )

    def _parse_query(self, query_text: str) -> Dict[str, Any]:
        """
        Parse natural language query to extract intent and entities.
        """
        parsed = {
            "intent": "list",
            "entities": {},
            "query_type": "transaction"
        }
        
        for intent, keywords in self.intent_patterns.items():
            if any(kw in query_text for kw in keywords):
                parsed["intent"] = intent
                break
        
        for keyword, ledger in self.ledger_keywords.items():
            if keyword in query_text:
                parsed["entities"]["ledger"] = ledger
                break
        
        amount_match = re.search(r'above\s+(\d+[,\d]*)', query_text)
        if amount_match:
            parsed["entities"]["amount_min"] = float(amount_match.group(1).replace(',', ''))
        
        amount_match = re.search(r'below\s+(\d+[,\d]*)', query_text)
        if amount_match:
            parsed["entities"]["amount_max"] = float(amount_match.group(1).replace(',', ''))
        
        if "q1" in query_text: parsed["entities"]["quarter"] = "Q1"
        elif "q2" in query_text: parsed["entities"]["quarter"] = "Q2"
        elif "q3" in query_text: parsed["entities"]["quarter"] = "Q3"
        elif "q4" in query_text: parsed["entities"]["quarter"] = "Q4"
        
        year_match = re.search(r'20\d{2}', query_text)
        if year_match:
            parsed["entities"]["year"] = int(year_match.group(0))
        
        return parsed

    def _extract_filters(self, parsed_query: Dict[str, Any], explicit_filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combine parsed entities and explicit filters.
        """
        filters = explicit_filters.copy() if explicit_filters else {}
        entities = parsed_query.get("entities", {})
        
        if "ledger" in entities: filters["ledger"] = entities["ledger"]
        if "amount_min" in entities: filters["amount_min"] = entities["amount_min"]
        if "amount_max" in entities: filters["amount_max"] = entities["amount_max"]
        
        if "quarter" in entities and "year" in entities:
            quarter = entities["quarter"]
            year = entities["year"]
            quarter_dates = {
                "Q1": (f"{year}-04-01", f"{year}-06-30"),
                "Q2": (f"{year}-07-01", f"{year}-09-30"),
                "Q3": (f"{year}-10-01", f"{year}-12-31"),
                "Q4": (f"{year+1}-01-01", f"{year+1}-03-31")
            }
            if quarter in quarter_dates:
                filters["date_from"], filters["date_to"] = quarter_dates[quarter]
        
        return filters

    def _build_db_query(self, filters: Dict[str, Any], parsed: Dict[str, Any]) -> Any:
        """
        Build a database query.
        """
        query = supabase.table("transactions").select("*").is_("deleted_at", "null")
        
        if "sheet_id" in filters: query = query.eq("sheet_id", filters["sheet_id"])
        if "ledger" in filters: query = query.eq("ledger", filters["ledger"])
        if "type" in filters: query = query.eq("type", filters["type"])
        if "date_from" in filters: query = query.gte("date", filters["date_from"])
        if "date_to" in filters: query = query.lte("date", filters["date_to"])
        if "amount_min" in filters: query = query.gte("amount", filters["amount_min"])
        if "amount_max" in filters: query = query.lte("amount", filters["amount_max"])
        
        query = query.order("date", desc=True).limit(100)
        return query

    def _execute_query(self, query: Any) -> List[Dict[str, Any]]:
        """
        Execute the database query.
        """
        try:
            response = query.execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []

    def _get_rag_context(self, query_text: str) -> List[str]:
        """
        Retrieve relevant legal/compliance context using RAG (Vector Search).
        """
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_service.generate_embedding(query_text)
            
            # Perform vector similarity search via Supabase RPC
            # Assuming 'match_law_chunks' function exists in Supabase
            params = {
                "query_embedding": query_embedding,
                "match_threshold": 0.7,
                "match_count": 3
            }
            response = supabase.rpc("match_law_chunks", params).execute()
            
            if response.data:
                return [item["content"] for item in response.data]
            
            # Fallback to keyword matching if vector search fails or returns empty
            law_references = []
            if "gst" in query_text:
                law_references.append("CGST Act, 2017 - Section 16 (Input Tax Credit)")
            if "tds" in query_text:
                law_references.append("Income Tax Act, 1961 - Section 194C (Payments to Contractors)")
            
            return law_references
            
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            return []

    def _assemble_response(self, result_data: List[Dict[str, Any]], law_references: List[str], query_text: str, parsed: Dict[str, Any]) -> QueryResult:
        """
        Assemble the final QueryResult.
        """
        intent = parsed.get("intent", "list")
        
        if intent == "aggregate":
            total_amount = sum(float(t.get("amount", 0)) for t in result_data)
            summary = f"Total: ₹{total_amount:,.2f} across {len(result_data)} transactions"
        else:
            summary = f"Found {len(result_data)} transactions"
            if result_data:
                total_amount = sum(float(t.get("amount", 0)) for t in result_data)
                summary += f" with total amount ₹{total_amount:,.2f}"
        
        return QueryResult(
            table=result_data,
            summary=summary,
            law_references=law_references if law_references else None
        )

    def validate_query(self, query_text: str) -> Dict[str, Any]:
        """
        Validate a natural language query.
        """
        if not query_text or len(query_text.strip()) == 0:
            return {"is_valid": False, "error": "Query cannot be empty"}
        
        if len(query_text) > 500:
            return {"is_valid": False, "error": "Query too long (max 500 characters)"}
        
        dangerous_patterns = ["drop", "delete", "truncate", "alter", "create", "insert", "update"]
        query_lower = query_text.lower()
        
        for pattern in dangerous_patterns:
            if pattern in query_lower:
                return {"is_valid": False, "error": f"Potentially dangerous keyword detected: {pattern}"}
        
        return {"is_valid": True}
