from typing import List, Dict, Any, Optional
from backend.models.rag_models import RetrievalResult

class PromptBuilder:
    """
    Module for constructing law-grounded, compliance-safe prompts.
    Merges user query, retrieved context, templates, and metadata.
    """

    # Base System Prompt enforcing role and safety
    SYSTEM_PROMPT = """
    You are 'Eagle Eyed', an expert AI Chartered Accountant assistant.
    Your role is to provide accurate, law-grounded answers based strictly on the provided context.
    
    Guidelines:
    1.  **Strict Adherence**: Answer ONLY based on the provided 'Context'. Do not hallucinate or use outside knowledge unless it is general accounting principles.
    2.  **Citation**: Cite the specific section, rule, or notification from the context when making a claim.
    3.  **Safety**: If the context does not contain the answer, state "I cannot find the answer in the provided documents."
    4.  **Tone**: Professional, precise, and authoritative yet helpful.
    5.  **Disclaimer**: Always imply that this is an AI-assisted interpretation and professional review is recommended for critical decisions.
    """

    # Template for RAG queries
    RAG_TEMPLATE = """
    Context:
    {context_str}
    
    User Query:
    {query}
    
    Answer:
    """

    # Template for Compliance Checks
    COMPLIANCE_TEMPLATE = """
    You are checking for compliance violations.
    
    Rules/Laws:
    {law_context}
    
    Transaction Data:
    {transaction_data}
    
    Task:
    Identify if the transaction violates any of the above rules.
    If yes, explain why and cite the rule.
    If no, state "Compliant".
    """

    def build_rag_prompt(self, query: str, retrieval_results: List[RetrievalResult]) -> str:
        """
        Constructs a prompt for RAG-based Q&A.
        
        Args:
            query: The user's question.
            retrieval_results: List of retrieved chunks from the vector store.
            
        Returns:
            Formatted prompt string.
        """
        context_str = self._format_context(retrieval_results)
        
        return self.RAG_TEMPLATE.format(
            context_str=context_str,
            query=query
        )

    def build_compliance_prompt(self, transaction_data: Dict[str, Any], law_context: List[RetrievalResult]) -> str:
        """
        Constructs a prompt for checking transaction compliance against laws.
        
        Args:
            transaction_data: Dictionary containing transaction details.
            law_context: List of relevant law chunks.
            
        Returns:
            Formatted prompt string.
        """
        context_str = self._format_context(law_context)
        transaction_str = str(transaction_data) # Convert dict to string representation
        
        return self.COMPLIANCE_TEMPLATE.format(
            law_context=context_str,
            transaction_data=transaction_str
        )

    def _format_context(self, results: List[RetrievalResult]) -> str:
        """
        Formats retrieved results into a single context string with metadata.
        """
        context_parts = []
        for i, res in enumerate(results, 1):
            # Include source metadata for citation
            source_info = f"[Source {i}: {res.metadata.get('source', 'Unknown')} - {res.metadata.get('section', '')}]"
            context_parts.append(f"{source_info}\n{res.text}")
            
        return "\n\n".join(context_parts)

    def get_system_prompt(self) -> str:
        """
        Returns the standard system prompt.
        """
        return self.SYSTEM_PROMPT.strip()
