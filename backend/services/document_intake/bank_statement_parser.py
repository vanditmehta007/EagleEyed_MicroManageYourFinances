# backend/services/document_intake/bank_statement_parser.py

from typing import List, Dict, Any
from fastapi import UploadFile
import csv
import io
from backend.utils.logger import logger
from backend.utils.date_utils import DateUtils

class BankStatementParser:
    """
    Parser for bank statements (PDF, CSV, Excel, etc.).
    Provides a high‑level API to convert a raw statement file into a list of
    normalized transaction dictionaries.
    """

    def __init__(self) -> None:
        # Common column name variations
        self.column_patterns = {
            "date": ["date", "transaction date", "txn date", "value date"],
            "description": ["description", "narration", "particulars", "details", "remarks"],
            "amount": ["amount", "transaction amount", "txn amount"],
            "debit": ["debit", "withdrawal", "dr"],
            "credit": ["credit", "deposit", "cr"],
            "balance": ["balance", "closing balance", "available balance"]
        }

    async def parse(self, file: UploadFile) -> List[Dict[str, Any]]:
        """
        Entry point to parse an uploaded bank statement file.
        """
        try:
            filename = file.filename.lower() if file.filename else ""
            
            # Read file content
            content = await file.read()
            
            if filename.endswith('.csv'):
                return self._parse_csv(content)
            elif filename.endswith(('.xlsx', '.xls')):
                return self._parse_excel(content)
            elif filename.endswith('.pdf'):
                return self._parse_pdf(content)
            else:
                logger.warning(f"Unsupported file format: {filename}")
                return []
                
        except Exception as e:
            logger.error(f"Bank statement parsing failed: {e}")
            return []

    def _parse_csv(self, content: bytes) -> List[Dict[str, Any]]:
        """
        Parse CSV bank statement.
        """
        try:
            csv_data = content.decode('utf-8')
            reader = csv.reader(io.StringIO(csv_data))
            
            rows = list(reader)
            if not rows:
                return []
            
            # Detect columns from header
            header_row = rows[0]
            column_map = self._detect_columns(header_row)
            
            # Parse transactions
            transactions = []
            for row in rows[1:]:
                if not any(row):  # Skip empty rows
                    continue
                
                txn = self._normalize_transaction(row, column_map)
                if txn:
                    transactions.append(txn)
            
            return transactions
            
        except Exception as e:
            logger.error(f"CSV parsing failed: {e}")
            return []

    def _parse_excel(self, content: bytes) -> List[Dict[str, Any]]:
        """
        Parse Excel bank statement.
        """
        try:
            import openpyxl
            workbook = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
            sheet = workbook.active
            
            # Get all rows
            rows = [[cell.value for cell in row] for row in sheet.iter_rows()]
            
            if not rows:
                return []
            
            # Detect columns from header
            header_row = rows[0]
            column_map = self._detect_columns(header_row)
            
            # Parse transactions
            transactions = []
            for row in rows[1:]:
                if not any(row):  # Skip empty rows
                    continue
                
                txn = self._normalize_transaction(row, column_map)
                if txn:
                    transactions.append(txn)
            
            return transactions
            
        except Exception as e:
            logger.error(f"Excel parsing failed: {e}")
            return []

    def _parse_pdf(self, content: bytes) -> List[Dict[str, Any]]:
        """
        Parse PDF bank statement.
        """
        # TODO: Implement PDF parsing using pdfplumber or tabula
        logger.warning("PDF parsing not yet implemented - requires OCR/table extraction")
        return []

    def _detect_columns(self, header_row: List[Any]) -> Dict[str, int]:
        """
        Determine the column indices for required fields.
        """
        column_map = {}
        
        # Normalize header row
        normalized_headers = [str(h).lower().strip() if h else "" for h in header_row]
        
        # Match patterns
        for field, patterns in self.column_patterns.items():
            for idx, header in enumerate(normalized_headers):
                if any(pattern in header for pattern in patterns):
                    column_map[field] = idx
                    break
        
        return column_map

    def _normalize_transaction(self, row: List[Any], column_map: Dict[str, int]) -> Dict[str, Any]:
        """
        Convert a raw row into a normalized transaction dictionary.
        """
        try:
            # Extract values
            date_val = row[column_map["date"]] if "date" in column_map else None
            desc_val = row[column_map["description"]] if "description" in column_map else ""
            
            # Handle amount (could be in single column or separate debit/credit)
            amount = 0.0
            txn_type = "debit"
            
            if "amount" in column_map:
                amount = float(row[column_map["amount"]]) if row[column_map["amount"]] else 0.0
                # Negative amount = debit, positive = credit
                if amount < 0:
                    amount = abs(amount)
                    txn_type = "debit"
                else:
                    txn_type = "credit"
            elif "debit" in column_map and "credit" in column_map:
                debit = float(row[column_map["debit"]]) if row[column_map["debit"]] else 0.0
                credit = float(row[column_map["credit"]]) if row[column_map["credit"]] else 0.0
                
                if debit > 0:
                    amount = debit
                    txn_type = "debit"
                elif credit > 0:
                    amount = credit
                    txn_type = "credit"
            
            balance = float(row[column_map["balance"]]) if "balance" in column_map and row[column_map["balance"]] else 0.0
            
            # Parse date
            parsed_date = DateUtils.parse_date(str(date_val)) if date_val else None
            
            return {
                "date": parsed_date,
                "description": str(desc_val).strip(),
                "amount": abs(amount),
                "type": txn_type,
                "balance": balance,
                "mode": "BANK"
            }
            
        except Exception as e:
            logger.error(f"Transaction normalization failed: {e}")
            return None