import re
from typing import Dict, Optional, Tuple, Any

class GSTUtils:
    """
    Helper utilities for Goods and Services Tax (GST) related operations.
    
    Includes:
    - GSTIN Validation
    - GST Rate Detection
    - Tax Calculation (Reverse Calculation, Breakup)
    - State Code Mapping
    """

    # GST State Codes Mapping
    STATE_CODES = {
        "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh",
        "05": "Uttarakhand", "06": "Haryana", "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
        "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur",
        "15": "Mizoram", "16": "Tripura", "17": "Meghalaya", "18": "Assam", "19": "West Bengal",
        "20": "Jharkhand", "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh",
        "24": "Gujarat", "25": "Daman and Diu", "26": "Dadra and Nagar Haveli", "27": "Maharashtra",
        "28": "Andhra Pradesh", "29": "Karnataka", "30": "Goa", "31": "Lakshadweep", "32": "Kerala",
        "33": "Tamil Nadu", "34": "Puducherry", "35": "Andaman and Nicobar Islands", "36": "Telangana",
        "37": "Andhra Pradesh (New)", "38": "Ladakh", "97": "Other Territory", "99": "Centre Jurisdiction"
    }

    # Common GST Rates
    GST_RATES = [0.0, 5.0, 12.0, 18.0, 28.0]

    @staticmethod
    def validate_gstin(gstin: str) -> bool:
        """
        Validate the format of a GSTIN (Goods and Services Tax Identification Number).
        
        Format: 2 digits (State Code) + 10 chars (PAN) + 1 digit (Entity No) + 1 char (Z) + 1 char (Check Code)
        Example: 22AAAAA0000A1Z5
        
        Args:
            gstin: The GSTIN string to validate.
            
        Returns:
            True if valid format, False otherwise.
        """
        if not gstin:
            return False
            
        # Regex for GSTIN format
        # \d{2} - State Code
        # [A-Z]{5} - PAN Alphabets
        # \d{4} - PAN Numbers
        # [A-Z]{1} - PAN Last char
        # [1-9A-Z]{1} - Entity Number
        # Z - Default char
        # [0-9A-Z]{1} - Check sum digit
        pattern = r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
        
        return bool(re.match(pattern, gstin))

    @staticmethod
    def get_state_from_gstin(gstin: str) -> Optional[str]:
        """
        Extract the state name from the GSTIN.
        
        Args:
            gstin: The GSTIN string.
            
        Returns:
            State name or None if invalid.
        """
        if not GSTUtils.validate_gstin(gstin):
            return None
            
        state_code = gstin[:2]
        return GSTUtils.STATE_CODES.get(state_code)

    @staticmethod
    def calculate_tax_breakup(amount: float, rate: float, is_interstate: bool = False) -> Dict[str, float]:
        """
        Calculate CGST, SGST, IGST based on taxable amount and rate.
        
        Args:
            amount: Taxable amount (base value).
            rate: GST Rate (e.g., 18.0).
            is_interstate: True if IGST applies, False for CGST+SGST.
            
        Returns:
            Dictionary with 'cgst', 'sgst', 'igst', 'total_tax', 'total_amount'.
        """
        tax_amount = round(amount * (rate / 100), 2)
        
        if is_interstate:
            return {
                "cgst": 0.0,
                "sgst": 0.0,
                "igst": tax_amount,
                "total_tax": tax_amount,
                "total_amount": round(amount + tax_amount, 2)
            }
        else:
            half_tax = round(tax_amount / 2, 2)
            return {
                "cgst": half_tax,
                "sgst": half_tax,
                "igst": 0.0,
                "total_tax": round(half_tax * 2, 2), # Sum of halves to avoid rounding issues
                "total_amount": round(amount + (half_tax * 2), 2)
            }

    @staticmethod
    def reverse_calculate_tax(total_amount: float, rate: float) -> Dict[str, float]:
        """
        Calculate base amount and tax from the total inclusive amount.
        
        Args:
            total_amount: Total amount including tax.
            rate: GST Rate (e.g., 18.0).
            
        Returns:
            Dictionary with 'base_amount' and 'tax_amount'.
        """
        if rate == 0:
            return {"base_amount": total_amount, "tax_amount": 0.0}
            
        base_amount = round(total_amount / (1 + (rate / 100)), 2)
        tax_amount = round(total_amount - base_amount, 2)
        
        return {
            "base_amount": base_amount,
            "tax_amount": tax_amount
        }

    @staticmethod
    def detect_gst_rate(base_amount: float, tax_amount: float) -> Optional[float]:
        """
        Detect the likely GST rate based on base and tax amounts.
        Matches against standard rates (0, 5, 12, 18, 28).
        
        Args:
            base_amount: Taxable value.
            tax_amount: Tax value.
            
        Returns:
            Detected rate or None if no match found within tolerance.
        """
        if base_amount == 0:
            return 0.0 if tax_amount == 0 else None
            
        calculated_rate = (tax_amount / base_amount) * 100
        
        # Check against standard rates with a small tolerance
        tolerance = 0.5
        for rate in GSTUtils.GST_RATES:
            if abs(calculated_rate - rate) <= tolerance:
                return rate
                
        return None

    @staticmethod
    def determine_supply_type(supplier_gstin: str, recipient_gstin: str) -> str:
        """
        Determine if supply is Interstate or Intrastate.
        
        Args:
            supplier_gstin: Supplier's GSTIN.
            recipient_gstin: Recipient's GSTIN.
            
        Returns:
            "Interstate" or "Intrastate" or "Unknown".
        """
        if not (GSTUtils.validate_gstin(supplier_gstin) and GSTUtils.validate_gstin(recipient_gstin)):
            return "Unknown"
            
        supplier_state = supplier_gstin[:2]
        recipient_state = recipient_gstin[:2]
        
        if supplier_state == recipient_state:
            return "Intrastate"
        else:
            return "Interstate"
