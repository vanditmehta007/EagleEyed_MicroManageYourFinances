import re
from typing import Optional, Tuple, Union

class AmountUtils:
    """
    Helper utilities for parsing, normalizing, and formatting currency amounts.
    
    Provides functionality for:
    - Cleaning and parsing amount strings (including Indian formats)
    - Detecting Credit/Debit nature
    - Formatting numbers to Indian currency style
    - Handling negative values and parentheses
    """

    @staticmethod
    def clean_amount_string(amount_str: str) -> str:
        """
        Removes currency symbols, commas, and whitespace from an amount string.
        
        Args:
            amount_str: The raw amount string (e.g., "₹ 1,23,456.00").
            
        Returns:
            Cleaned string suitable for float conversion (e.g., "123456.00").
        """
        if not amount_str:
            return "0"
            
        # Remove currency symbols (₹, $, etc.) and commas
        # Keep digits, decimal point, and negative sign/parentheses
        cleaned = re.sub(r'[^\d\.\-\(\)]', '', str(amount_str))
        return cleaned

    @staticmethod
    def parse_amount(amount_str: Union[str, float, int]) -> float:
        """
        Parses an amount string into a float.
        Handles Indian numbering format (commas), parentheses for negatives, and 'Cr'/'Dr' suffixes.
        
        Args:
            amount_str: The raw amount input.
            
        Returns:
            Float value. Returns 0.0 if parsing fails.
        """
        if isinstance(amount_str, (int, float)):
            return float(amount_str)
            
        if not amount_str:
            return 0.0
            
        original_str = str(amount_str).strip().upper()
        
        # Check for Cr/Dr suffix
        is_credit = False
        is_debit = False
        if original_str.endswith("CR"):
            is_credit = True
        elif original_str.endswith("DR"):
            is_debit = True
            
        # Clean the string
        cleaned = AmountUtils.clean_amount_string(original_str)
        
        # Handle parentheses for negative numbers (accounting format)
        if '(' in cleaned and ')' in cleaned:
            cleaned = cleaned.replace('(', '-').replace(')', '')
            
        try:
            value = float(cleaned)
            
            # Apply sign based on suffix if present (Context dependent, usually Credit is positive income, Debit is negative expense)
            # However, in bank statements: Credit = +, Debit = -
            # In accounting ledgers: Credit = Liability/Income, Debit = Asset/Expense
            # Here we assume Bank Statement convention: Credit (+), Debit (-)
            
            if is_debit:
                value = -abs(value)
            elif is_credit:
                value = abs(value)
                
            return value
        except ValueError:
            return 0.0

    @staticmethod
    def detect_transaction_type(amount: float, description: str = "") -> str:
        """
        Determines if a transaction is 'credit' or 'debit' based on amount sign or description.
        
        Args:
            amount: The transaction amount.
            description: Optional description to aid detection.
            
        Returns:
            "credit" or "debit".
        """
        # Simple sign check
        if amount < 0:
            return "debit"
        if amount > 0:
            return "credit"
            
        # If amount is 0 (or positive but ambiguous), check description
        desc_upper = description.upper()
        if "DEBIT" in desc_upper or "DR" in desc_upper:
            return "debit"
        if "CREDIT" in desc_upper or "CR" in desc_upper:
            return "credit"
            
        return "debit" # Default to debit if unknown? Or maybe 'unknown'

    @staticmethod
    def format_indian_currency(amount: float) -> str:
        """
        Formats a number into Indian currency format (e.g., 1,23,456.00).
        
        Args:
            amount: The float amount.
            
        Returns:
            Formatted string.
        """
        amount_str = f"{abs(amount):.2f}"
        parts = amount_str.split('.')
        integer_part = parts[0]
        decimal_part = parts[1]
        
        if len(integer_part) <= 3:
            formatted_int = integer_part
        else:
            # Last 3 digits
            last_three = integer_part[-3:]
            remaining = integer_part[:-3]
            # Group remaining by 2
            # Reverse, chunk by 2, reverse back
            remaining_grouped = re.sub(r"(\d)(?=(\d{2})+(?!\d))", r"\1,", remaining)
            formatted_int = f"{remaining_grouped},{last_three}"
            
        sign = "-" if amount < 0 else ""
        return f"{sign}₹{formatted_int}.{decimal_part}"

    @staticmethod
    def extract_amount_from_text(text: str) -> Optional[float]:
        """
        Extracts the first valid currency amount found in a text string.
        
        Args:
            text: Text containing an amount.
            
        Returns:
            Extracted float amount or None.
        """
        # Regex to find currency-like patterns
        # Matches: ₹ 1,23,456.00, Rs. 500, 1200.50
        pattern = r'(?:Rs\.?|₹)?\s*[\d,]+\.\d{2}\b'
        match = re.search(pattern, text)
        if match:
            return AmountUtils.parse_amount(match.group(0))
        return None
