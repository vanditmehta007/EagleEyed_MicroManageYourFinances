# backend/services/document_intake/gst_json_parser.py

from typing import List, Dict, Any
from fastapi import UploadFile
import json
from backend.utils.logger import logger
from backend.utils.date_utils import DateUtils

class GSTJSONParser:
    """
    Parser for GST JSON files (GSTR-1, GSTR-2A, GSTR-2B, etc.).
    Extracts transaction data from GST portal JSON exports.
    """

    def __init__(self) -> None:
        pass

    async def parse(self, file: UploadFile) -> List[Dict[str, Any]]:
        """
        Parse GST JSON file and extract transactions.
        """
        try:
            content = await file.read()
            data = json.loads(content)
            
            # Detect GST return type
            if "b2b" in data or "b2ba" in data:
                return self._parse_gstr1(data)
            elif "docdata" in data:
                return self._parse_gstr2b(data)
            else:
                return self._parse_generic_gst(data)
                
        except Exception as e:
            logger.error(f"GST JSON parsing failed: {e}")
            return []

    def _parse_gstr1(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse GSTR-1 (Sales) JSON format.
        """
        transactions = []
        
        # Parse B2B invoices
        if "b2b" in data:
            for entry in data["b2b"]:
                gstin = entry.get("ctin", "")
                
                for invoice in entry.get("inv", []):
                    inv_num = invoice.get("inum", "")
                    inv_date = invoice.get("idt", "")
                    
                    for item in invoice.get("itms", []):
                        for item_detail in item.get("itm_det", []):
                            txn = {
                                "date": DateUtils.parse_date(inv_date),
                                "description": f"B2B Sale - {gstin}",
                                "invoice_number": inv_num,
                                "gstin": gstin,
                                "amount": float(item_detail.get("txval", 0)),
                                "gst_rate": float(item_detail.get("rt", 0)),
                                "igst": float(item_detail.get("iamt", 0)),
                                "cgst": float(item_detail.get("camt", 0)),
                                "sgst": float(item_detail.get("samt", 0)),
                                "type": "credit",
                                "source": "GSTR-1"
                            }
                            transactions.append(txn)
        
        # Parse B2C (small) invoices
        if "b2cs" in data:
            for entry in data["b2cs"]:
                txn = {
                    "date": DateUtils.parse_date(entry.get("sply_ty", "")),
                    "description": "B2C Sale",
                    "amount": float(entry.get("txval", 0)),
                    "gst_rate": float(entry.get("rt", 0)),
                    "type": "credit",
                    "source": "GSTR-1"
                }
                transactions.append(txn)
        
        return transactions

    def _parse_gstr2b(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse GSTR-2B (Auto-populated ITC) JSON format.
        """
        transactions = []
        
        if "docdata" in data:
            doc_data = data["docdata"]
            
            # Parse B2B purchases
            if "b2b" in doc_data:
                for entry in doc_data["b2b"]:
                    gstin = entry.get("ctin", "")
                    
                    for invoice in entry.get("inv", []):
                        inv_num = invoice.get("inum", "")
                        inv_date = invoice.get("idt", "")
                        
                        for item in invoice.get("items", []):
                            txn = {
                                "date": DateUtils.parse_date(inv_date),
                                "description": f"B2B Purchase - {gstin}",
                                "invoice_number": inv_num,
                                "gstin": gstin,
                                "amount": float(item.get("txval", 0)),
                                "gst_rate": float(item.get("rt", 0)),
                                "igst": float(item.get("iamt", 0)),
                                "cgst": float(item.get("camt", 0)),
                                "sgst": float(item.get("samt", 0)),
                                "type": "debit",
                                "source": "GSTR-2B"
                            }
                            transactions.append(txn)
        
        return transactions

    def _parse_generic_gst(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse generic GST JSON format.
        """
        transactions = []
        
        # Try to extract transactions from common structures
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    txn = self._extract_transaction_from_dict(item)
                    if txn:
                        transactions.append(txn)
        elif isinstance(data, dict):
            # Check for nested transaction arrays
            for key, value in data.items():
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            txn = self._extract_transaction_from_dict(item)
                            if txn:
                                transactions.append(txn)
        
        return transactions

    def _extract_transaction_from_dict(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract transaction from a dictionary with flexible key matching.
        """
        try:
            # Try to find common fields
            date = item.get("date") or item.get("invoice_date") or item.get("idt")
            amount = item.get("amount") or item.get("taxable_value") or item.get("txval") or 0
            
            if not date or not amount:
                return None
            
            return {
                "date": DateUtils.parse_date(str(date)),
                "description": item.get("description", "GST Transaction"),
                "invoice_number": item.get("invoice_number", ""),
                "gstin": item.get("gstin", ""),
                "amount": float(amount),
                "gst_rate": float(item.get("gst_rate", 0)),
                "type": item.get("type", "debit"),
                "source": "GST JSON"
            }
        except Exception:
            return None