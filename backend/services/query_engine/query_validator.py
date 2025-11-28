# backend/services/query_engine/query_validator.py

from typing import Dict, Any, List, Optional
import re
from datetime import datetime
from backend.utils.logger import logger


class QueryValidator:
    """
    Validates queries, filters, SQL fragments, and AI-generated responses for safety and correctness.
    
    Ensures:
    - SQL injection prevention
    - Filter value validation (dates, amounts, strings)
    - AI response citation requirements
    - CA-facing safety rules (no hallucinated laws, professional tone)
    - Input sanitization
    
    Critical for production safety in a financial compliance application.
    """

    def __init__(self) -> None:
        # TODO: Initialize validation rules and patterns
        self._init_validation_patterns()
        logger.info("QueryValidator initialized")

    def validate_query(self, query_text: str) -> Dict[str, Any]:
        """
        Validate a natural language query before processing.
        """
        errors = []
        warnings = []
        
        # TODO: Sanitize query text
        sanitized_query = self.sanitize_input(query_text)
        
        # TODO: Check for empty or too short queries
        if not sanitized_query:
            errors.append("Query is empty")
        elif len(sanitized_query) < 3:
            errors.append("Query is too short")
            
        # TODO: Check query length limits
        if len(sanitized_query) > 500:
            errors.append("Query exceeds maximum length of 500 characters")
            
        # TODO: Check for suspicious patterns (SQL keywords, script tags)
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, sanitized_query, re.IGNORECASE):
                warnings.append("Query contains suspicious SQL-like patterns")
                break
                
        if "<script>" in sanitized_query.lower():
            errors.append("Query contains potentially malicious script tags")
            
        # TODO: Return validation result
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sanitized_query": sanitized_query
        }

    def validate_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate extracted filters for correctness and security.
        """
        errors = []
        warnings = []
        
        # TODO: Validate date formats and ranges using self._validate_date_range
        date_errors = self._validate_date_range(filters.get("date_from"), filters.get("date_to"))
        errors.extend(date_errors)
        
        # TODO: Validate amount ranges using self._validate_amount_range
        amount_errors = self._validate_amount_range(filters.get("amount_min"), filters.get("amount_max"))
        errors.extend(amount_errors)
        
        # TODO: Validate string filters using self._validate_string_filter
        for key, value in filters.items():
            if isinstance(value, str) and key not in ["date_from", "date_to"]:
                string_errors = self._validate_string_filter(key, value)
                errors.extend(string_errors)
        
        # TODO: Check for logical inconsistencies
        # (Already handled partially in range checks)
        
        # TODO: Return validation result
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def validate_sql_fragment(self, sql_fragment: str) -> Dict[str, Any]:
        """
        Validate SQL fragment for injection attacks and safety.
        """
        errors = []
        warnings = []
        
        # TODO: Check for dangerous SQL keywords (DROP, DELETE, UPDATE, INSERT)
        # TODO: Check for comment patterns (-- , /* */)
        # TODO: Check for union attacks
        # TODO: Validate parameterization
        
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, sql_fragment, re.IGNORECASE):
                errors.append(f"SQL fragment contains dangerous pattern: {pattern}")
        
        # TODO: Return validation result
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def validate_ai_response(
        self, 
        response: str, 
        law_context: List[str],
        require_citations: bool = True
    ) -> Dict[str, Any]:
        """
        Validate AI-generated response for CA-facing safety.
        """
        errors = []
        warnings = []
        
        # TODO: Check for citations using self._check_citations
        citation_check = self._check_citations(response)
        if require_citations and not citation_check["has_citations"]:
            warnings.append("Response lacks required legal citations")
            
        # TODO: Verify citations are from law_context (no hallucinations)
        hallucinated = self._verify_citations_grounded(citation_check["citations"], law_context)
        if hallucinated:
            warnings.append(f"Response contains potentially hallucinated citations: {', '.join(hallucinated)}")
            
        # TODO: Check professional tone using self._check_professional_tone
        tone_warnings = self._check_professional_tone(response)
        warnings.extend(tone_warnings)
        
        # TODO: Check for prohibited content
        # (Basic check implemented in tone check)
        
        # TODO: Return validation result
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "citation_check": citation_check
        }

    def _init_validation_patterns(self) -> None:
        """
        Initialize regex patterns for validation.
        """
        # TODO: Define SQL injection patterns
        self.sql_injection_patterns = [
            r"(\bDROP\b|\bDELETE\b|\bUPDATE\b|\bINSERT\b|\bALTER\b|\bTRUNCATE\b)",
            r"(--|\/\*|\*\/)",
            r"(\bUNION\b.*\bSELECT\b)",
            r"(\bEXEC\b|\bEXECUTE\b)",
            r";"  # Statement chaining
        ]
        
        # TODO: Define date format patterns
        self.date_pattern = r"^\d{4}-\d{2}-\d{2}$"
        
        # TODO: Define citation patterns
        self.citation_pattern = r"(Section \d+[A-Z]*|Rule \d+|Act \d{4}|Notification \d+|Article \d+)"
        
        # Informal language patterns
        self.informal_patterns = [
            r"\b(lol|omg|dude|bro|idk|tbh)\b",
            r"(!{2,})",  # Multiple exclamation marks
            r"\b(gonna|wanna)\b"
        ]

    def _validate_date_range(self, date_from: Optional[str], date_to: Optional[str]) -> List[str]:
        """
        Validate date range filters.
        """
        errors = []
        
        # TODO: Check date format using regex
        if date_from and not re.match(self.date_pattern, date_from):
            errors.append(f"Invalid date_from format: {date_from}. Expected YYYY-MM-DD.")
        if date_to and not re.match(self.date_pattern, date_to):
            errors.append(f"Invalid date_to format: {date_to}. Expected YYYY-MM-DD.")
            
        # TODO: Parse dates and check if date_from <= date_to
        if date_from and date_to and not errors:
            try:
                d_from = datetime.strptime(date_from, "%Y-%m-%d")
                d_to = datetime.strptime(date_to, "%Y-%m-%d")
                
                if d_from > d_to:
                    errors.append("date_from cannot be later than date_to")
                
                # TODO: Check for unreasonable date ranges (e.g., future dates, dates before 1900)
                if d_from.year < 1900 or d_to.year < 1900:
                    errors.append("Dates cannot be before year 1900")
                
                # Future date check (optional, depending on context, but usually queries are historical)
                # if d_from > datetime.now() + timedelta(days=365):
                #     errors.append("Date is too far in the future")
                    
            except ValueError:
                errors.append("Invalid date value")
                
        # TODO: Return errors
        return errors

    def _validate_amount_range(self, amount_min: Optional[float], amount_max: Optional[float]) -> List[str]:
        """
        Validate amount range filters.
        """
        errors = []
        
        # TODO: Check if amounts are numeric
        # (Type hinting suggests float, but runtime check might be needed if input is loose)
        if amount_min is not None and not isinstance(amount_min, (int, float)):
             errors.append("amount_min must be a number")
        if amount_max is not None and not isinstance(amount_max, (int, float)):
             errors.append("amount_max must be a number")
             
        if errors:
            return errors

        # TODO: Check if amount_min <= amount_max
        if amount_min is not None and amount_max is not None:
            if amount_min > amount_max:
                errors.append("amount_min cannot be greater than amount_max")
        
        # TODO: Check for unreasonable values (negative amounts for expenses, extremely large values)
        if amount_min is not None and amount_min < 0:
            errors.append("amount_min cannot be negative")
        if amount_max is not None and amount_max < 0:
            errors.append("amount_max cannot be negative")
            
        # TODO: Return errors
        return errors

    def _validate_string_filter(self, field_name: str, value: str) -> List[str]:
        """
        Validate string filter values for SQL injection and format.
        """
        errors = []
        
        # TODO: Check string length limits
        if len(value) > 255:
            errors.append(f"Value for {field_name} exceeds maximum length")
            
        # TODO: Check for SQL injection patterns
        # TODO: Check for script tags and XSS attempts
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                errors.append(f"Value for {field_name} contains suspicious patterns")
                break
                
        if "<script>" in value.lower():
            errors.append(f"Value for {field_name} contains malicious content")
            
        # TODO: Return errors
        return errors

    def _check_citations(self, response: str) -> Dict[str, Any]:
        """
        Check if response contains proper citations.
        """
        # TODO: Use regex to find citation patterns
        citations = re.findall(self.citation_pattern, response, re.IGNORECASE)
        
        # TODO: Extract citation strings
        # TODO: Return dict with has_citations and citations list
        return {
            "has_citations": len(citations) > 0,
            "citations": list(set(citations))  # Unique citations
        }

    def _check_professional_tone(self, response: str) -> List[str]:
        """
        Check if response maintains professional tone suitable for CAs.
        """
        warnings = []
        
        # TODO: Check for informal language (slang, emojis, etc.)
        for pattern in self.informal_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                warnings.append("Response contains informal language")
                break
        
        # TODO: Check for overly casual phrases
        # TODO: Check for absolute statements without qualifiers
        # (Simplified check)
        
        # TODO: Return warnings
        return warnings

    def _verify_citations_grounded(self, citations: List[str], law_context: List[str]) -> List[str]:
        """
        Verify that all citations in the response are from the provided law context.
        """
        hallucinated = []
        
        # TODO: For each citation, check if it appears in law_context
        context_text = " ".join(law_context).lower()
        
        for citation in citations:
            # Simple containment check
            # Normalize citation for comparison
            normalized_citation = citation.lower()
            
            # Check if the citation (or a reasonable part of it) exists in context
            # This is a heuristic; exact matching might be too strict
            if normalized_citation not in context_text:
                hallucinated.append(citation)
                
        # TODO: Flag citations not found in law_context as hallucinated
        # TODO: Return list of hallucinated citations
        return hallucinated

    def sanitize_input(self, input_text: str) -> str:
        """
        Sanitize user input to prevent injection attacks.
        """
        if not input_text:
            return ""
            
        # TODO: Normalize whitespace
        sanitized = " ".join(input_text.split())
        
        # TODO: Remove or escape dangerous characters
        # For a query engine, we mostly want to prevent control characters
        # and ensure it's printable text.
        # We don't want to aggressively strip SQL keywords here because they might be part of natural language
        # (e.g., "select the best option"), but we validate against injection patterns later.
        
        # TODO: Trim to reasonable length
        sanitized = sanitized[:1000]
        
        # TODO: Return sanitized string
        return sanitized
