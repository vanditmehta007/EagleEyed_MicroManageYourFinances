# backend/services/document_intake/invoice_parser.py

from typing import List, Dict, Any, Optional
from fastapi import UploadFile
from backend.utils.logger import logger
from backend.utils.date_utils import DateUtils
import re


class InvoiceParser:
    """
    Parser for invoices and expense bills (PDF, images).
    Extracts key information like vendor, amount, date, GST details.
    """

    def __init__(self) -> None:
        # Common vendor name patterns (first few lines of invoice)
        self.vendor_keywords = [
            "pvt", "ltd", "limited", "private", "company", 
            "corporation", "enterprises", "services", "solutions"
        ]

    async def parse(self, file: UploadFile) -> Dict[str, Any]:
        """
        Parse an invoice file and extract structured data.
        """
        try:
            filename = file.filename.lower() if file.filename else ""
            content = await file.read()
            
            if filename.endswith('.pdf'):
                return self._parse_pdf(content)
            elif filename.endswith(('.jpg', '.jpeg', '.png')):
                return self._parse_image(content)
            else:
                logger.warning(f"Unsupported invoice format: {filename}")
                return {}
                
        except Exception as e:
            logger.error(f"Invoice parsing failed: {e}")
            return {}

    def _parse_pdf(self, content: bytes) -> Dict[str, Any]:
        """
        Parse PDF invoice using text extraction.
        """
        try:
            import PyPDF2
            import io
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            
            # Extract text from all pages
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            # Extract invoice details using pattern matching
            invoice_data = self._extract_invoice_details(text)
            
            logger.info(f"Successfully parsed PDF invoice: {invoice_data.get('invoice_number', 'Unknown')}")
            
            return invoice_data
            
        except Exception as e:
            logger.error(f"PDF invoice parsing failed: {e}")
            return {}

    def _parse_image(self, content: bytes) -> Dict[str, Any]:
        """
        Parse image invoice using OCR.
        """
        # TODO: Implement OCR using Tesseract or cloud OCR service
        # For production, integrate with:
        # - Tesseract OCR (pytesseract)
        # - Google Cloud Vision API
        # - AWS Textract
        # - Azure Computer Vision
        logger.warning("Image invoice parsing requires OCR - not yet implemented")
        return {
            "vendor": "Unknown",
            "invoice_number": "",
            "date": None,
            "amount": 0.0,
            "gst_amount": 0.0,
            "note": "OCR required for image processing"
        }

    def _extract_invoice_details(self, text: str) -> Dict[str, Any]:
        """
        Extract invoice details from text using pattern matching.
        """
        invoice_data = {
            "vendor": "",
            "invoice_number": "",
            "date": None,
            "amount": 0.0,
            "gst_amount": 0.0,
            "gstin": "",
            "pan": "",
            "line_items": []
        }
        
        # Extract vendor name (usually in first few lines)
        vendor_name = self._extract_vendor_name(text)
        if vendor_name:
            invoice_data["vendor"] = vendor_name
        
        # Extract invoice number
        inv_patterns = [
            r'invoice\s*(?:no|number|#)?[:\s]*([A-Z0-9\-/]+)',
            r'bill\s*(?:no|number|#)?[:\s]*([A-Z0-9\-/]+)',
            r'inv\s*(?:no|#)?[:\s]*([A-Z0-9\-/]+)'
        ]
        
        for pattern in inv_patterns:
            inv_match = re.search(pattern, text, re.IGNORECASE)
            if inv_match:
                invoice_data["invoice_number"] = inv_match.group(1).strip()
                break
        
        # Extract GSTIN (15-character format)
        gstin_match = re.search(r'GSTIN[:\s]*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})', text, re.IGNORECASE)
        if gstin_match:
            invoice_data["gstin"] = gstin_match.group(1)
        
        # Extract PAN (10-character format)
        pan_match = re.search(r'PAN[:\s]*([A-Z]{5}[0-9]{4}[A-Z]{1})', text, re.IGNORECASE)
        if pan_match:
            invoice_data["pan"] = pan_match.group(1)
        
        # Extract total amount (multiple patterns for robustness)
        amount_patterns = [
            r'total[:\s]*₹?\s*([0-9,]+\.?[0-9]*)',
            r'grand\s*total[:\s]*₹?\s*([0-9,]+\.?[0-9]*)',
            r'net\s*amount[:\s]*₹?\s*([0-9,]+\.?[0-9]*)',
            r'amount\s*payable[:\s]*₹?\s*([0-9,]+\.?[0-9]*)',
            r'total\s*amount[:\s]*₹?\s*([0-9,]+\.?[0-9]*)'
        ]
        
        for pattern in amount_patterns:
            amount_match = re.search(pattern, text, re.IGNORECASE)
            if amount_match:
                amount_str = amount_match.group(1).replace(',', '')
                try:
                    invoice_data["amount"] = float(amount_str)
                    break
                except ValueError:
                    continue
        
        # Extract GST amount (sum of CGST, SGST, IGST)
        gst_total = 0.0
        gst_patterns = [
            r'(?:GST|IGST|CGST|SGST)[:\s]*₹?\s*([0-9,]+\.?[0-9]*)',
            r'tax[:\s]*₹?\s*([0-9,]+\.?[0-9]*)'
        ]
        
        for pattern in gst_patterns:
            gst_matches = re.findall(pattern, text, re.IGNORECASE)
            for match in gst_matches:
                try:
                    gst_total += float(match.replace(',', ''))
                except ValueError:
                    continue
        
        if gst_total > 0:
            invoice_data["gst_amount"] = round(gst_total, 2)
        
        # Extract date (multiple formats)
        date_patterns = [
            r'date[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
            r'invoice\s*date[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
            r'bill\s*date[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
            r'dated[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})'
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, text, re.IGNORECASE)
            if date_match:
                try:
                    invoice_data["date"] = DateUtils.parse_date(date_match.group(1))
                    break
                except:
                    continue
        
        # Extract line items (simplified - looks for item descriptions and amounts)
        line_items = self._extract_line_items(text)
        if line_items:
            invoice_data["line_items"] = line_items
        
        return invoice_data
    
    def _extract_vendor_name(self, text: str) -> str:
        """
        Extract vendor name from invoice text.
        Typically found in the first few lines.
        """
        lines = text.split('\n')
        
        # Check first 10 lines for vendor name
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            
            # Skip empty lines and common headers
            if not line or len(line) < 3:
                continue
            
            # Check if line contains vendor keywords
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in self.vendor_keywords):
                # Clean up the vendor name
                vendor_name = line.strip()
                # Remove common prefixes
                vendor_name = re.sub(r'^(M/s|Ms|Mr|Mrs)\.?\s*', '', vendor_name, flags=re.IGNORECASE)
                return vendor_name
        
        # Fallback: return first non-empty line if no keywords found
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) > 3:
                return line
        
        return ""
    
    def _extract_line_items(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract line items from invoice (simplified extraction).
        """
        line_items = []
        
        # This is a simplified implementation
        # In production, use table detection or more sophisticated parsing
        
        # Look for patterns like: Item Description ... Qty ... Rate ... Amount
        item_pattern = r'([A-Za-z\s]+)\s+([0-9]+)\s+([0-9,]+\.?[0-9]*)\s+([0-9,]+\.?[0-9]*)'
        
        matches = re.findall(item_pattern, text)
        
        for match in matches[:10]:  # Limit to 10 items to avoid false positives
            try:
                line_items.append({
                    "description": match[0].strip(),
                    "quantity": int(match[1]),
                    "rate": float(match[2].replace(',', '')),
                    "amount": float(match[3].replace(',', ''))
                })
            except (ValueError, IndexError):
                continue
        
        return line_items