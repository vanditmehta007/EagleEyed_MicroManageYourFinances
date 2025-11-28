# backend/services/transaction_extraction_service.py

from typing import List, Dict, Any
from backend.services.ocr.ocr_service import OCRService
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger
import re
from datetime import datetime

class TransactionExtractionService:
    """
    Service to extract transaction data from bank statement documents.
    Uses OCR to read PDF content and AI to parse transactions.
    """
    
    def __init__(self):
        self.ocr_service = OCRService()
    
    def extract_transactions_from_document(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Extract transactions from a bank statement document.
        
        Args:
            document_id: ID of the document to process
            
        Returns:
            List of transaction dictionaries
        """
        try:
            # Fetch document from database
            doc_response = supabase.table("documents").select("*").eq("id", document_id).single().execute()
            
            if not doc_response.data:
                logger.error(f"Document {document_id} not found")
                return []
            
            document = doc_response.data
            
            # Check if document is a bank statement
            if document.get("file_type") != "bank_statement":
                logger.warning(f"Document {document_id} is not a bank statement")
                return []
            
            # Get file path from storage
            file_path = document.get("file_path")
            if not file_path:
                logger.error(f"No file path for document {document_id}")
                return []
            
            # Download file from Supabase storage
            file_data = supabase.storage.from_("documents").download(file_path)
            
            # Extract text using OCR
            # Note: This is a simplified implementation
            # In production, you'd want to use more sophisticated methods
            text = self._extract_text_from_pdf(file_data)
            
            # Parse transactions from text
            transactions = self._parse_transactions(text, document_id)
            
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to extract transactions from document {document_id}: {e}")
            return []
    
    def _extract_text_from_pdf(self, file_data: bytes) -> str:
        """
        Extract text from PDF using OCR.
        """
        try:
            import pytesseract
            import pdf2image
            from PIL import Image
            import io
            
            # Convert PDF to images
            images = pdf2image.convert_from_bytes(file_data)
            
            text = ""
            for img in images:
                text += pytesseract.image_to_string(img) + "\n"
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""
    
    def _parse_transactions(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """
        Parse transaction data from extracted text.
        This is a simplified parser - in production, use AI/ML models for better accuracy.
        """
        transactions = []
        
        # Common patterns for bank statements
        # Date patterns: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD
        date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})'
        
        # Amount pattern: numbers with optional commas and decimals
        amount_pattern = r'([\d,]+\.?\d{0,2})'
        
        # Split text into lines
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to find date and amount in the line
            date_match = re.search(date_pattern, line)
            amount_matches = re.findall(amount_pattern, line)
            
            if date_match and amount_matches:
                try:
                    # Parse date
                    date_str = date_match.group(1)
                    transaction_date = self._parse_date(date_str)
                    
                    # Get description (text between date and amounts)
                    description = line[date_match.end():].strip()
                    
                    # Determine debit/credit
                    # Usually last two amounts are debit and credit
                    debit = None
                    credit = None
                    balance = None
                    
                    if len(amount_matches) >= 2:
                        # Clean amounts
                        amounts = [float(amt.replace(',', '')) for amt in amount_matches if amt]
                        
                        # Heuristic: if 3 amounts, likely debit, credit, balance
                        if len(amounts) == 3:
                            debit = amounts[0] if amounts[0] > 0 else None
                            credit = amounts[1] if amounts[1] > 0 else None
                            balance = amounts[2]
                        elif len(amounts) == 2:
                            # Could be debit+balance or credit+balance
                            # Simple heuristic: larger number is balance
                            if amounts[0] > amounts[1]:
                                balance = amounts[0]
                                credit = amounts[1]
                            else:
                                debit = amounts[0]
                                balance = amounts[1]
                    
                    transaction = {
                        "document_id": document_id,
                        "date": transaction_date.isoformat() if transaction_date else None,
                        "description": description[:200],  # Limit description length
                        "debit": debit,
                        "credit": credit,
                        "balance": balance,
                        "raw_line": line[:500]  # Store raw line for reference
                    }
                    
                    # Apply flagging logic
                    transaction = self._apply_flagging(transaction)
                    
                    transactions.append(transaction)
                    
                except Exception as e:
                    logger.debug(f"Failed to parse line: {line[:50]}... Error: {e}")
                    continue
        
        return transactions

    def _apply_flagging(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply rule-based flagging to a transaction.
        """
        debit = transaction.get("debit")
        credit = transaction.get("credit")
        description = transaction.get("description", "").lower()
        
        is_flagged = False
        flag_reason = None
        
        # Determine the transaction amount
        amount = debit if debit is not None else (credit if credit is not None else 0)
        
        # Flagging Rules
        if amount and amount > 100000:
            is_flagged = True
            flag_reason = "High value transaction (> 1 Lakh)"
        elif "cash" in description:
            is_flagged = True
            flag_reason = "Cash transaction detected"
        elif "suspense" in description:
            is_flagged = True
            flag_reason = "Suspense account usage"
        elif "personal" in description:
            is_flagged = True
            flag_reason = "Potential personal expense"
        elif amount and amount > 1000 and amount % 5000 == 0:
             is_flagged = True
             flag_reason = "Round figure amount detected"

        transaction["is_flagged"] = is_flagged
        transaction["flag_reason"] = flag_reason
        return transaction
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string in various formats.
        """
        formats = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%d/%m/%y",
            "%d-%m-%y",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # If all fail, return current date
        return datetime.now()
    
    def get_transactions_by_client(self, client_id: str) -> Dict[str, Any]:
        """
        Get all transactions for a client, organized by year and month.
        """
        try:
            # Get all bank statement documents for this client
            docs_response = supabase.table("documents").select("*").eq("client_id", client_id).eq("file_type", "bank_statement").execute()
            
            if not docs_response.data:
                return {}
            
            # Organize by year and month
            organized = {}
            
            for doc in docs_response.data:
                # Extract transactions from this document
                transactions = self.extract_transactions_from_document(doc["id"])
                
                # Organize by date
                for txn in transactions:
                    if not txn.get("date"):
                        continue
                    
                    txn_date = datetime.fromisoformat(txn["date"])
                    year = str(txn_date.year)
                    month = txn_date.strftime("%B")  # Full month name
                    
                    if year not in organized:
                        organized[year] = {}
                    if month not in organized[year]:
                        organized[year][month] = []
                    
                    organized[year][month].append(txn)
            
            return organized
            
        except Exception as e:
            logger.error(f"Failed to get transactions for client {client_id}: {e}")
            return {}
