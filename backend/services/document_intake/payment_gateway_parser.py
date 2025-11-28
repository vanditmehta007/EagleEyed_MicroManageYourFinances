# backend/services/document_intake/payment_gateway_parser.py

from typing import List, Dict, Any
from fastapi import UploadFile
import pandas as pd
import json
import io
from datetime import datetime
from backend.utils.logger import logger
from backend.utils.date_utils import DateUtils


class PaymentGatewayParser:
    """
    Parser for transaction exports from popular payment gateways:
        - Razorpay
        - Paytm
        - Stripe
        - PhonePe
        - UPI (generic CSV/Excel/JSON)

    Each public method accepts the raw uploaded file and returns a list of
    normalized transaction dictionaries with a common schema:
        {
            "date": str,
            "gateway": str,
            "transaction_id": str,
            "amount": float,
            "currency": str,
            "status": str,
            "payer": str,
            "payee": str,
            "description": str,
            "raw": dict   # optional raw payload for debugging
        }

    The implementation is intentionally skeletal – ``TODO`` placeholders mark
    where the actual parsing logic should be added.
    """

    def __init__(self) -> None:
        # TODO: Initialise any CSV/Excel readers (pandas, openpyxl) or JSON parsers.
        # Initialize pandas for CSV/Excel parsing
        self.supported_formats = ['.csv', '.xlsx', '.xls', '.json']
        logger.info("PaymentGatewayParser initialized")

    async def _read_file_content(self, file: UploadFile) -> pd.DataFrame:
        """
        Helper method to read file content into a pandas DataFrame.
        Supports CSV, Excel, and JSON formats.
        """
        try:
            filename = file.filename.lower() if file.filename else ""
            content = await file.read()
            
            if filename.endswith('.csv'):
                return pd.read_csv(io.BytesIO(content))
            elif filename.endswith(('.xlsx', '.xls')):
                return pd.read_excel(io.BytesIO(content))
            elif filename.endswith('.json'):
                data = json.loads(content.decode('utf-8'))
                # Handle both array of objects and nested JSON
                if isinstance(data, list):
                    return pd.DataFrame(data)
                elif isinstance(data, dict) and 'items' in data:
                    return pd.DataFrame(data['items'])
                else:
                    return pd.DataFrame([data])
            else:
                logger.error(f"Unsupported file format: {filename}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Failed to read file content: {e}")
            return pd.DataFrame()

    async def parse_razorpay(self, file: UploadFile) -> List[Dict[str, Any]]:
        """
        Parse a Razorpay export (CSV/Excel/JSON) and normalise entries.

        Args:
            file: Uploaded export file.

        Returns:
            List of normalized transaction dicts.
        """
        # TODO: Detect file type, read content, map Razorpay fields to the common schema.
        try:
            df = await self._read_file_content(file)
            
            if df.empty:
                return []
            
            transactions = []
            
            # Razorpay field mapping
            # Common fields: Payment ID, Created At, Amount, Status, Email, Contact, Description
            for _, row in df.iterrows():
                try:
                    transaction = {
                        "date": self._parse_date(row.get('Created At', row.get('created_at', ''))),
                        "gateway": "razorpay",
                        "transaction_id": str(row.get('Payment ID', row.get('id', ''))),
                        "amount": float(row.get('Amount', row.get('amount', 0))) / 100,  # Razorpay stores in paise
                        "currency": str(row.get('Currency', row.get('currency', 'INR'))),
                        "status": str(row.get('Status', row.get('status', 'unknown'))).lower(),
                        "payer": str(row.get('Email', row.get('email', row.get('Contact', '')))),
                        "payee": "merchant",  # Razorpay is always merchant receiving
                        "description": str(row.get('Description', row.get('notes', ''))),
                        "raw": row.to_dict()
                    }
                    transactions.append(transaction)
                except Exception as e:
                    logger.error(f"Failed to parse Razorpay row: {e}")
                    continue
            
            logger.info(f"Parsed {len(transactions)} Razorpay transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Razorpay parsing failed: {e}")
            return []

    async def parse_paytm(self, file: UploadFile) -> List[Dict[str, Any]]:
        """
        Parse a Paytm export (CSV/Excel/JSON) and normalise entries.

        Args:
            file: Uploaded export file.

        Returns:
            List of normalized transaction dicts.
        """
        # TODO: Implement Paytm-specific field mapping.
        try:
            df = await self._read_file_content(file)
            
            if df.empty:
                return []
            
            transactions = []
            
            # Paytm field mapping
            # Common fields: Transaction ID, Date, Amount, Status, Payer Name, Description
            for _, row in df.iterrows():
                try:
                    transaction = {
                        "date": self._parse_date(row.get('Date', row.get('Transaction Date', ''))),
                        "gateway": "paytm",
                        "transaction_id": str(row.get('Transaction ID', row.get('Order ID', ''))),
                        "amount": float(row.get('Amount', row.get('Transaction Amount', 0))),
                        "currency": "INR",  # Paytm is India-specific
                        "status": str(row.get('Status', row.get('Transaction Status', 'unknown'))).lower(),
                        "payer": str(row.get('Payer Name', row.get('Customer Name', ''))),
                        "payee": str(row.get('Payee Name', 'merchant')),
                        "description": str(row.get('Description', row.get('Remarks', ''))),
                        "raw": row.to_dict()
                    }
                    transactions.append(transaction)
                except Exception as e:
                    logger.error(f"Failed to parse Paytm row: {e}")
                    continue
            
            logger.info(f"Parsed {len(transactions)} Paytm transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Paytm parsing failed: {e}")
            return []

    async def parse_stripe(self, file: UploadFile) -> List[Dict[str, Any]]:
        """
        Parse a Stripe export (CSV/Excel/JSON) and normalise entries.

        Args:
            file: Uploaded export file.

        Returns:
            List of normalized transaction dicts.
        """
        # TODO: Implement Stripe-specific field mapping.
        try:
            df = await self._read_file_content(file)
            
            if df.empty:
                return []
            
            transactions = []
            
            # Stripe field mapping
            # Common fields: id, Created (UTC), Amount, Currency, Status, Description, Customer Email
            for _, row in df.iterrows():
                try:
                    # Stripe amounts are in cents
                    amount = float(row.get('Amount', row.get('amount', 0)))
                    currency = str(row.get('Currency', row.get('currency', 'usd'))).upper()
                    
                    # Convert from cents to main currency unit
                    if currency in ['JPY', 'KRW']:  # Zero-decimal currencies
                        amount_normalized = amount
                    else:
                        amount_normalized = amount / 100
                    
                    transaction = {
                        "date": self._parse_date(row.get('Created (UTC)', row.get('created', ''))),
                        "gateway": "stripe",
                        "transaction_id": str(row.get('id', row.get('charge_id', ''))),
                        "amount": amount_normalized,
                        "currency": currency,
                        "status": str(row.get('Status', row.get('status', 'unknown'))).lower(),
                        "payer": str(row.get('Customer Email', row.get('customer_email', ''))),
                        "payee": "merchant",
                        "description": str(row.get('Description', row.get('description', ''))),
                        "raw": row.to_dict()
                    }
                    transactions.append(transaction)
                except Exception as e:
                    logger.error(f"Failed to parse Stripe row: {e}")
                    continue
            
            logger.info(f"Parsed {len(transactions)} Stripe transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Stripe parsing failed: {e}")
            return []

    async def parse_phonepe(self, file: UploadFile) -> List[Dict[str, Any]]:
        """
        Parse a PhonePe export (CSV/Excel/JSON) and normalise entries.

        Args:
            file: Uploaded export file.

        Returns:
            List of normalized transaction dicts.
        """
        # TODO: Implement PhonePe-specific field mapping.
        try:
            df = await self._read_file_content(file)
            
            if df.empty:
                return []
            
            transactions = []
            
            # PhonePe field mapping
            # Common fields: Transaction ID, Date & Time, Amount, Status, Merchant Name, UPI ID
            for _, row in df.iterrows():
                try:
                    transaction = {
                        "date": self._parse_date(row.get('Date & Time', row.get('Transaction Date', ''))),
                        "gateway": "phonepe",
                        "transaction_id": str(row.get('Transaction ID', row.get('UTR', ''))),
                        "amount": float(row.get('Amount', row.get('Transaction Amount', 0))),
                        "currency": "INR",  # PhonePe is India-specific
                        "status": str(row.get('Status', row.get('Transaction Status', 'unknown'))).lower(),
                        "payer": str(row.get('UPI ID', row.get('Sender UPI', ''))),
                        "payee": str(row.get('Merchant Name', row.get('Receiver UPI', 'merchant'))),
                        "description": str(row.get('Description', row.get('Remarks', ''))),
                        "raw": row.to_dict()
                    }
                    transactions.append(transaction)
                except Exception as e:
                    logger.error(f"Failed to parse PhonePe row: {e}")
                    continue
            
            logger.info(f"Parsed {len(transactions)} PhonePe transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"PhonePe parsing failed: {e}")
            return []

    async def parse_upi(self, file: UploadFile) -> List[Dict[str, Any]]:
        """
        Parse a generic UPI transaction export (CSV/Excel/JSON) and normalise entries.

        Args:
            file: Uploaded export file.

        Returns:
            List of normalized transaction dicts.
        """
        # TODO: Implement generic UPI parsing logic (detect columns, map to schema).
        try:
            df = await self._read_file_content(file)
            
            if df.empty:
                return []
            
            transactions = []
            
            # Generic UPI field mapping - try to detect common column names
            # Common patterns: Date, Amount, UPI ID, Transaction ID, Status, Remarks
            date_cols = [col for col in df.columns if any(x in col.lower() for x in ['date', 'time', 'timestamp'])]
            amount_cols = [col for col in df.columns if any(x in col.lower() for x in ['amount', 'value', 'sum'])]
            id_cols = [col for col in df.columns if any(x in col.lower() for x in ['id', 'utr', 'reference', 'transaction'])]
            status_cols = [col for col in df.columns if 'status' in col.lower()]
            upi_cols = [col for col in df.columns if 'upi' in col.lower()]
            desc_cols = [col for col in df.columns if any(x in col.lower() for x in ['description', 'remark', 'note', 'narration'])]
            
            for _, row in df.iterrows():
                try:
                    transaction = {
                        "date": self._parse_date(row.get(date_cols[0], '') if date_cols else ''),
                        "gateway": "upi",
                        "transaction_id": str(row.get(id_cols[0], '') if id_cols else ''),
                        "amount": float(row.get(amount_cols[0], 0) if amount_cols else 0),
                        "currency": "INR",  # UPI is India-specific
                        "status": str(row.get(status_cols[0], 'unknown') if status_cols else 'unknown').lower(),
                        "payer": str(row.get(upi_cols[0], '') if upi_cols else ''),
                        "payee": str(row.get(upi_cols[1], 'merchant') if len(upi_cols) > 1 else 'merchant'),
                        "description": str(row.get(desc_cols[0], '') if desc_cols else ''),
                        "raw": row.to_dict()
                    }
                    transactions.append(transaction)
                except Exception as e:
                    logger.error(f"Failed to parse UPI row: {e}")
                    continue
            
            logger.info(f"Parsed {len(transactions)} generic UPI transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Generic UPI parsing failed: {e}")
            return []
    
    def _parse_date(self, date_str: str) -> str:
        """
        Helper method to parse various date formats into ISO format.
        """
        if not date_str:
            return datetime.utcnow().isoformat()
        
        try:
            # Try using DateUtils if available
            parsed_date = DateUtils.parse_date(str(date_str))
            if parsed_date:
                return parsed_date
        except:
            pass
        
        # Fallback: try common formats
        common_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%d-%m-%Y %H:%M:%S',
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%d %b %Y',
            '%Y-%m-%dT%H:%M:%S',
        ]
        
        for fmt in common_formats:
            try:
                dt = datetime.strptime(str(date_str), fmt)
                return dt.isoformat()
            except:
                continue
        
        # If all fails, return current timestamp
        logger.warning(f"Could not parse date: {date_str}, using current timestamp")
        return datetime.utcnow().isoformat()