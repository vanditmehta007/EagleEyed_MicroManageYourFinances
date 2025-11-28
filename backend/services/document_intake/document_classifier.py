# backend/services/document_intake/document_classifier.py

from fastapi import UploadFile
from typing import List, Dict
from backend.utils.logger import logger


class DocumentClassifier:
    """
    Simple heuristic‑based classifier that predicts the document category
    (e.g., bank_statement, invoice, gst_json, expense, sales, purchase, payroll)
    based on the uploaded file's name, MIME type, or minimal content inspection.

    The implementation is intentionally lightweight – real‑world usage would replace
    the heuristics with a trained ML model or more sophisticated rule engine.
    """

    def __init__(self) -> None:
        # TODO: Load any external resources (e.g., keyword lists, regex patterns)
        # Define comprehensive keyword mappings for each document type
        self.keyword_mappings: Dict[str, List[str]] = {
            "bank_statement": [
                "bank", "statement", "bs", "account_statement", 
                "passbook", "transaction_history", "bank_stmt"
            ],
            "invoice": [
                "invoice", "inv", "bill", "tax_invoice", 
                "proforma", "commercial_invoice", "sales_invoice"
            ],
            "gst_json": [
                "gst", "gstjson", "gstr", "gstr1", "gstr2", 
                "gstr3b", "gst_return", "json"
            ],
            "expense": [
                "expense", "receipt", "voucher", "petty_cash",
                "reimbursement", "claim"
            ],
            "sales": [
                "sales", "sale", "revenue", "sales_register",
                "sales_report", "sales_data"
            ],
            "purchase": [
                "purchase", "purch", "procurement", "purchase_order",
                "po", "purchase_register", "vendor_invoice"
            ],
            "payroll": [
                "payroll", "salary", "pay", "wage", "payslip",
                "pay_slip", "salary_slip", "compensation"
            ],
            "tax_return": [
                "itr", "tax_return", "income_tax", "return_filing",
                "tax_filing", "itr1", "itr2", "itr3", "itr4"
            ],
            "balance_sheet": [
                "balance_sheet", "bs", "financial_position",
                "assets_liabilities", "balance"
            ],
            "profit_loss": [
                "profit_loss", "p&l", "pnl", "income_statement",
                "profit_and_loss", "pl_statement"
            ],
            "tds_certificate": [
                "tds", "form16", "form_16", "tds_certificate",
                "26as", "form_26as", "tax_deduction"
            ]
        }
        
        # MIME type mappings for additional validation
        self.mime_type_hints: Dict[str, str] = {
            "application/json": "gst_json",
            "application/pdf": None,  # PDF can be any type
            "text/csv": None,  # CSV can be any type
            "application/vnd.ms-excel": None,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": None
        }
        
        logger.info("DocumentClassifier initialized with keyword mappings")

    def classify(self, file: UploadFile) -> str:
        """
        Predict the document type.

        Args:
            file: The uploaded file object.

        Returns:
            A string identifier for the document category. One of:
            "bank_statement", "invoice", "gst_json", "expense",
            "sales", "purchase", "payroll", "tax_return", "balance_sheet",
            "profit_loss", "tds_certificate", or "unknown".
        """
        # TODO: Extract filename and lower‑case it for heuristic checks
        filename = file.filename.lower() if file.filename else ""
        content_type = file.content_type.lower() if file.content_type else ""
        
        logger.debug(f"Classifying file: {filename}, content_type: {content_type}")
        
        # TODO: Basic keyword heuristics – extend as needed
        # Check filename against all keyword mappings
        for doc_type, keywords in self.keyword_mappings.items():
            if any(keyword in filename for keyword in keywords):
                logger.info(f"Classified '{filename}' as '{doc_type}' based on filename keywords")
                return doc_type
        
        # Additional heuristic: Check file extension for JSON files
        if filename.endswith('.json'):
            # JSON files are likely GST returns
            logger.info(f"Classified '{filename}' as 'gst_json' based on .json extension")
            return "gst_json"
        
        # Additional heuristic: Check MIME type
        if content_type in self.mime_type_hints:
            mime_hint = self.mime_type_hints[content_type]
            if mime_hint:
                logger.info(f"Classified '{filename}' as '{mime_hint}' based on MIME type")
                return mime_hint
        
        # TODO: Optionally inspect file content (e.g., first few bytes or text)
        # For now, fall back to unknown
        logger.warning(f"Could not classify '{filename}' - returning 'unknown'")
        return "unknown"
    
    def classify_batch(self, files: List[UploadFile]) -> Dict[str, str]:
        """
        Classify multiple files at once.
        
        Args:
            files: List of uploaded file objects.
            
        Returns:
            Dictionary mapping filename to document type.
        """
        results = {}
        for file in files:
            filename = file.filename if file.filename else f"file_{len(results)}"
            doc_type = self.classify(file)
            results[filename] = doc_type
        
        logger.info(f"Batch classified {len(files)} files")
        return results
    
    def get_supported_types(self) -> List[str]:
        """
        Get list of all supported document types.
        
        Returns:
            List of document type identifiers.
        """
        return list(self.keyword_mappings.keys()) + ["unknown"]