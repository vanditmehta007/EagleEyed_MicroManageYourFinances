from datetime import datetime, date
from typing import Optional, Tuple, List
import re
from dateutil import parser

class DateUtils:
    """
    Helper utilities for date parsing, manipulation, and financial year calculations.
    
    Provides functionality for:
    - Parsing dates from various string formats (DD/MM/YYYY, etc.)
    - Fuzzy date extraction from text
    - Determining Financial Year and Quarters
    - Generating date ranges for periods
    """

    @staticmethod
    def parse_date(date_str: str) -> Optional[date]:
        """
        Parses a date string into a python date object.
        Prioritizes DD/MM/YYYY format common in India.
        
        Args:
            date_str: The date string to parse.
            
        Returns:
            Date object or None if parsing fails.
        """
        if not date_str:
            return None
            
        try:
            # Try specific Indian formats first
            for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y'):
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            
            # Fallback to dateutil parser
            return parser.parse(date_str, dayfirst=True).date()
        except Exception:
            return None

    @staticmethod
    def extract_date_fuzzy(text: str) -> Optional[date]:
        """
        Extracts the first valid date found in a text string using regex patterns.
        Useful for extracting dates from OCR text.
        
        Args:
            text: The text containing a potential date.
            
        Returns:
            The first extracted date object or None.
        """
        # Regex for common date patterns (DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD)
        # Matches: 31/12/2023, 31-12-2023, 2023-12-31, 1-Jan-2023
        patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # DD/MM/YYYY or DD-MM-YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD or YYYY-MM-DD
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b' # 12 Jan 2023
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parsed = DateUtils.parse_date(match.group(0))
                if parsed:
                    return parsed
        return None

    @staticmethod
    def get_financial_year(dt: date) -> str:
        """
        Returns the Financial Year string (e.g., "2023-24") for a given date.
        Indian FY starts from April 1st.
        
        Args:
            dt: The date object.
            
        Returns:
            Financial Year string.
        """
        if dt.month >= 4:
            return f"{dt.year}-{str(dt.year + 1)[-2:]}"
        else:
            return f"{dt.year - 1}-{str(dt.year)[-2:]}"

    @staticmethod
    def get_quarter(dt: date) -> str:
        """
        Returns the Quarter (Q1, Q2, Q3, Q4) for a given date based on Indian FY.
        Q1: Apr-Jun, Q2: Jul-Sep, Q3: Oct-Dec, Q4: Jan-Mar
        
        Args:
            dt: The date object.
            
        Returns:
            Quarter string.
        """
        month = dt.month
        if 4 <= month <= 6:
            return "Q1"
        elif 7 <= month <= 9:
            return "Q2"
        elif 10 <= month <= 12:
            return "Q3"
        else:
            return "Q4"

    @staticmethod
    def get_month_range(month: int, year: int) -> Tuple[date, date]:
        """
        Returns the start and end date for a specific month and year.
        
        Args:
            month: Month number (1-12).
            year: Year.
            
        Returns:
            Tuple of (start_date, end_date).
        """
        import calendar
        _, last_day = calendar.monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        return start_date, end_date

    @staticmethod
    def get_previous_month(dt: date) -> Tuple[int, int]:
        """
        Returns the previous month and its year.
        
        Args:
            dt: The reference date.
            
        Returns:
            Tuple of (month, year).
        """
        first = dt.replace(day=1)
        prev_month = first - __import__('datetime').timedelta(days=1)
        return prev_month.month, prev_month.year
