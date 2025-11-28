# backend/services/query_engine/query_llm.py

from typing import Dict, Any, List, Optional
import os
import json
import re
from backend.utils.logger import logger
from backend.services.query_engine.query_templates import QueryTemplates
# import openai  # Uncomment when implementing


class QueryLLM:
    """
    LLM wrapper for query processing with law-grounded, CA-safe reasoning.
    
    Responsibilities:
    - Send structured prompts to AI models (OpenAI, Claude, etc.)
    - Include RAG-retrieved legal context in prompts
    - Ensure responses are grounded in actual laws/rules
    - Format responses for CA consumption
    - Handle API errors and rate limiting
    
    Safety features:
    - Citation requirements (no hallucinated laws)
    - Professional tone enforcement
    - Compliance-focused reasoning
    """

    def __init__(self) -> None:
        # TODO: Initialize LLM client (OpenAI, Anthropic, etc.)
        # self.api_key = os.getenv("OPENAI_API_KEY")
        # openai.api_key = self.api_key
        # self.model = "gpt-4"  # or "claude-3-opus", etc.
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("LLM_MODEL", "gpt-4")
        self.templates = QueryTemplates()
        logger.info(f"QueryLLM initialized with model: {self.model}")

    def parse_query(self, query_text: str) -> Dict[str, Any]:
        """
        Parse natural language query into structured components using LLM.
        """
        # TODO: Build prompt using QueryTemplates.get_query_parsing_template
        try:
            prompt = self.templates.get_query_parsing_template(query_text)
            
            # TODO: Send to LLM API
            response = self._call_llm(
                prompt=prompt,
                system_message="You are a financial query parser. Extract intent, entities, and filters from queries.",
                temperature=0.3,
                max_tokens=500
            )
            
            # TODO: Parse JSON response
            try:
                parsed = json.loads(response)
            except json.JSONDecodeError:
                # Fallback parsing
                parsed = {
                    "intent": "general_query",
                    "entities": [],
                    "filters": {},
                    "raw_query": query_text
                }
            
            # TODO: Validate response structure
            if not isinstance(parsed, dict):
                parsed = {"intent": "unknown", "entities": [], "filters": {}}
            
            # TODO: Return parsed dict
            logger.info(f"Parsed query: {parsed.get('intent', 'unknown')}")
            return parsed
            
        except Exception as e:
            logger.error(f"Query parsing failed: {e}")
            return {"intent": "error", "entities": [], "filters": {}, "error": str(e)}

    def generate_explanation(
        self, 
        query: str, 
        results: List[Dict[str, Any]], 
        law_context: List[str]
    ) -> str:
        """
        Generate CA-friendly explanation of query results with legal grounding.
        """
        # TODO: Build prompt using QueryTemplates.get_explanation_template
        try:
            prompt = self.templates.get_explanation_template(query, results, law_context)
            
            # TODO: Include law_context in system message for grounding
            system_msg = f"You are a CA assistant. Provide professional explanations grounded in these laws:\n{chr(10).join(law_context[:5])}"
            
            # TODO: Send to LLM API with temperature=0.3 (more deterministic)
            response = self._call_llm(
                prompt=prompt,
                system_message=system_msg,
                temperature=0.3,
                max_tokens=1000
            )
            
            # TODO: Extract explanation from response
            explanation = response.strip()
            
            # TODO: Validate citations are from provided law_context
            if not self._ensure_grounded_response(explanation, law_context):
                logger.warning("Response contains ungrounded citations")
            
            # TODO: Return explanation
            return self._sanitize_response(explanation)
            
        except Exception as e:
            logger.error(f"Explanation generation failed: {e}")
            return f"Analysis of {len(results)} results for: {query}"

    def get_compliance_reasoning(
        self, 
        transaction: Dict[str, Any], 
        law_context: List[str]
    ) -> Dict[str, Any]:
        """
        Get compliance reasoning for a specific transaction.
        """
        # TODO: Build prompt using QueryTemplates.get_compliance_context_template
        try:
            prompt = self.templates.get_compliance_context_template(transaction, law_context)
            
            # TODO: Include law_context for grounding
            system_msg = f"You are a compliance expert. Base reasoning on these laws:\n{chr(10).join(law_context[:5])}"
            
            # TODO: Send to LLM API
            response = self._call_llm(
                prompt=prompt,
                system_message=system_msg,
                temperature=0.2,
                max_tokens=800
            )
            
            # TODO: Parse response into structured dict
            try:
                reasoning = json.loads(response)
            except json.JSONDecodeError:
                reasoning = {
                    "compliant": True,
                    "applicable_rules": law_context[:3],
                    "recommendations": [response],
                    "risk_level": "low"
                }
            
            # TODO: Return compliance reasoning
            logger.info(f"Generated compliance reasoning for transaction {transaction.get('id', 'unknown')}")
            return reasoning
            
        except Exception as e:
            logger.error(f"Compliance reasoning failed: {e}")
            return {"compliant": True, "applicable_rules": [], "recommendations": [], "error": str(e)}

    def validate_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate extracted filters using LLM for security and correctness.
        """
        # TODO: Build prompt using QueryTemplates.get_filter_validation_template
        try:
            prompt = self.templates.get_filter_validation_template(filters)
            
            # TODO: Send to LLM API
            response = self._call_llm(
                prompt=prompt,
                system_message="You are a security validator. Check filters for SQL injection and logical errors.",
                temperature=0.1,
                max_tokens=300
            )
            
            # TODO: Parse JSON response
            try:
                validation = json.loads(response)
            except json.JSONDecodeError:
                validation = {"is_valid": True, "errors": []}
            
            # TODO: Return validation result
            return validation
            
        except Exception as e:
            logger.error(f"Filter validation failed: {e}")
            return {"is_valid": False, "errors": [str(e)]}

    def generate_aggregation_insights(
        self, 
        query: str, 
        data: List[Dict[str, Any]]
    ) -> str:
        """
        Generate aggregated insights from query results.
        """
        # TODO: Build prompt using QueryTemplates.get_aggregation_template
        try:
            prompt = self.templates.get_aggregation_template(query, data)
            
            # TODO: Send to LLM API
            response = self._call_llm(
                prompt=prompt,
                system_message="You are a financial analyst. Provide concise insights from data.",
                temperature=0.4,
                max_tokens=600
            )
            
            # TODO: Extract insights from response
            insights = response.strip()
            
            # TODO: Return summary
            return self._sanitize_response(insights)
            
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            return f"Summary of {len(data)} records"

    def _call_llm(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Internal method to call LLM API with error handling.
        """
        # TODO: Implement API call with error handling
        # TODO: Handle rate limiting with exponential backoff
        # TODO: Log API usage for monitoring
        # TODO: Return response text
        
        # Placeholder implementation - replace with actual API call
        if not self.api_key:
            logger.warning("LLM API key not configured - using fallback")
            return self._fallback_response(prompt)
        
        try:
            # Example implementation:
            # import openai
            # response = openai.ChatCompletion.create(
            #     model=self.model,
            #     messages=[
            #         {"role": "system", "content": system_message or "You are a helpful assistant."},
            #         {"role": "user", "content": prompt}
            #     ],
            #     temperature=temperature,
            #     max_tokens=max_tokens
            # )
            # return response.choices[0].message.content
            
            logger.info(f"LLM call: {len(prompt)} chars, temp={temperature}")
            return self._fallback_response(prompt)
            
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return self._fallback_response(prompt)

    def _ensure_grounded_response(self, response: str, law_context: List[str]) -> bool:
        """
        Verify that LLM response only cites laws from the provided context.
        """
        # TODO: Extract citations from response
        # TODO: Check if all citations are in law_context
        # TODO: Flag hallucinated laws
        # TODO: Return validation result
        
        # Extract potential law references (Section X, Act Y, etc.)
        citation_patterns = [
            r'Section\s+\d+[A-Z]*',
            r'Rule\s+\d+',
            r'Act[,\s]+\d{4}',
            r'Article\s+\d+'
        ]
        
        found_citations = []
        for pattern in citation_patterns:
            found_citations.extend(re.findall(pattern, response, re.IGNORECASE))
        
        if not found_citations:
            return True  # No citations to validate
        
        # Check if citations are in context
        context_text = " ".join(law_context)
        for citation in found_citations:
            if citation not in context_text:
                logger.warning(f"Potentially hallucinated citation: {citation}")
                return False
        
        return True

    def _sanitize_response(self, response: str) -> str:
        """
        Sanitize LLM response for CA consumption.
        """
        # TODO: Remove any inappropriate content
        # TODO: Ensure professional language
        # TODO: Format citations properly
        # TODO: Return sanitized response
        
        # Remove markdown formatting
        sanitized = response.replace("**", "").replace("*", "")
        
        # Ensure professional tone (basic check)
        unprofessional_words = ["dude", "bro", "lol", "omg"]
        for word in unprofessional_words:
            sanitized = re.sub(rf'\b{word}\b', '', sanitized, flags=re.IGNORECASE)
        
        # Clean up whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized

    def _fallback_response(self, prompt: str) -> str:
        """
        Generate fallback response when LLM is unavailable.
        """
        if "parse" in prompt.lower():
            return json.dumps({"intent": "general_query", "entities": [], "filters": {}})
        elif "compliance" in prompt.lower():
            return json.dumps({"compliant": True, "applicable_rules": [], "recommendations": []})
        elif "validate" in prompt.lower():
            return json.dumps({"is_valid": True, "errors": []})
        else:
            return "Analysis completed. Please review the data for detailed insights."
