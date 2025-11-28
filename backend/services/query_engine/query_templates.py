# backend/services/query_engine/query_templates.py

from typing import Dict, Any


class QueryTemplates:
    """
    Prompt templates for natural language query processing.
    
    These templates are used with LLMs (e.g., OpenAI, Claude) to:
    - Parse natural language queries into structured filters
    - Generate SQL/Supabase queries
    - Explain results to CAs in plain language
    - Provide compliance context
    """

    @staticmethod
    def get_query_parsing_template(query: str) -> str:
        """
        Template for parsing natural language query into structured intent and entities.
        
        Args:
            query: The natural language query from the user.
            
        Returns:
            Formatted prompt for LLM.
        """
        return f"""You are a financial data analyst assistant. Parse the following natural language query into structured components.

Query: "{query}"

Extract and return a JSON object with the following fields:
{{
    "intent": "list|filter|aggregate|compliance_check|report",
    "entity_type": "transaction|client|sheet|document|vendor",
    "filters": {{
        "ledger": "string or null",
        "date_from": "YYYY-MM-DD or null",
        "date_to": "YYYY-MM-DD or null",
        "amount_min": "number or null",
        "amount_max": "number or null",
        "vendor": "string or null",
        "type": "credit|debit or null"
    }},
    "aggregation": "sum|count|average or null",
    "sort_by": "date|amount|ledger or null",
    "sort_order": "asc|desc or null"
}}

Only return the JSON object, no additional text."""

    @staticmethod
    def get_sql_generation_template(filters: Dict[str, Any], table: str) -> str:
        """
        Template for generating SQL/Supabase query from structured filters.
        
        Args:
            filters: Structured filter dict.
            table: Target table name.
            
        Returns:
            Formatted prompt for LLM.
        """
        return f"""Generate a Supabase query builder chain for the following filters.

Table: {table}
Filters: {filters}

Return Python code using Supabase query builder syntax. Example:
```python
query = supabase.table("{table}").select("*")
query = query.eq("type", "debit")
query = query.gte("amount", 50000)
query = query.order("date", desc=True)
```

Only return the Python code, no explanations."""

    @staticmethod
    def get_explanation_template(query: str, results: list, law_refs: list) -> str:
        """
        Template for generating CA-friendly explanation of query results.
        
        Args:
            query: Original natural language query.
            results: Query results (list of dicts).
            law_refs: Relevant law references from RAG.
            
        Returns:
            Formatted prompt for LLM.
        """
        result_count = len(results)
        return f"""You are a Chartered Accountant assistant. Explain the following query results in professional, clear language.

Original Query: "{query}"
Number of Results: {result_count}
Sample Results: {results[:5] if results else "No results found"}
Relevant Laws/Rules: {law_refs}

Provide a concise summary that includes:
1. What the query was asking for
2. Key findings from the results
3. Any compliance implications based on the law references
4. Recommended next steps for the CA (if applicable)

Keep the explanation professional and actionable."""

    @staticmethod
    def get_compliance_context_template(transaction_data: Dict[str, Any]) -> str:
        """
        Template for retrieving compliance context for a transaction.
        
        Args:
            transaction_data: Transaction details.
            
        Returns:
            Formatted prompt for RAG retrieval.
        """
        return f"""Identify relevant tax and compliance rules for this transaction:

Transaction Details:
- Description: {transaction_data.get('description', 'N/A')}
- Amount: {transaction_data.get('amount', 'N/A')}
- Ledger: {transaction_data.get('ledger', 'N/A')}
- Vendor: {transaction_data.get('vendor', 'N/A')}
- Date: {transaction_data.get('date', 'N/A')}

What GST, TDS, Income Tax, or other compliance rules apply to this transaction?"""

    @staticmethod
    def get_filter_validation_template(filters: Dict[str, Any]) -> str:
        """
        Template for validating extracted filters before query execution.
        
        Args:
            filters: Extracted filter dict.
            
        Returns:
            Formatted prompt for LLM.
        """
        return f"""Validate the following query filters for correctness and security.

Filters: {filters}

Check for:
1. Valid date formats (YYYY-MM-DD)
2. Reasonable amount ranges (no negative values unless debit)
3. Valid ledger names (no SQL injection attempts)
4. Logical consistency (date_from <= date_to)

Return a JSON object:
{{
    "is_valid": true|false,
    "errors": ["list of error messages"],
    "warnings": ["list of warnings"]
}}

Only return the JSON object."""

    @staticmethod
    def get_aggregation_template(query: str, data: list) -> str:
        """
        Template for generating aggregated insights from query results.
        
        Args:
            query: Original query.
            data: Query results.
            
        Returns:
            Formatted prompt for LLM.
        """
        return f"""Analyze the following financial data and provide aggregated insights.

Query: "{query}"
Data: {data}

Provide:
1. Total amount (if applicable)
2. Average transaction value
3. Transaction count
4. Top 3 vendors/ledgers by amount
5. Any notable patterns or anomalies

Format as a concise summary suitable for a CA dashboard."""
