from typing import Dict, Optional, Any, Tuple

class IncomeTaxUtils:
    """
    Helper utilities for Income Tax related lookups and rules.
    
    Includes:
    - TDS Rates and Thresholds
    - Section Descriptions
    - Cash Transaction Limits (40A(3), 269ST)
    - Depreciation Block Rates
    """

    # TDS Rates and Thresholds (FY 2023-24 / 2024-25)
    # Format: "Section": {"rate": float (percentage), "threshold": float (amount), "description": str}
    TDS_RATES = {
        "194C": {
            "rate_individual": 1.0,
            "rate_other": 2.0,
            "threshold_single": 30000.0,
            "threshold_aggregate": 100000.0,
            "description": "Payments to Contractors"
        },
        "194J": {
            "rate_technical": 2.0,
            "rate_professional": 10.0,
            "threshold": 30000.0,
            "description": "Fees for Professional or Technical Services"
        },
        "194I": {
            "rate_land_building": 10.0,
            "rate_plant_machinery": 2.0,
            "threshold": 240000.0,
            "description": "Rent"
        },
        "194H": {
            "rate": 5.0,
            "threshold": 15000.0,
            "description": "Commission or Brokerage"
        },
        "194Q": {
            "rate": 0.1,
            "threshold": 5000000.0,
            "description": "Purchase of Goods (Turnover > 10Cr)"
        }
    }

    # Depreciation Rates (Income Tax Act)
    DEPRECIATION_RATES = {
        "Building (Residential)": 5.0,
        "Building (Commercial)": 10.0,
        "Furniture and Fittings": 10.0,
        "Plant and Machinery": 15.0,
        "Computers and Software": 40.0,
        "Motor Vehicles (Personal)": 15.0,
        "Motor Vehicles (Commercial)": 30.0,
        "Intangible Assets": 25.0
    }

    @staticmethod
    def get_tds_details(section: str) -> Optional[Dict[str, Any]]:
        """
        Get TDS rate and threshold for a specific section.
        
        Args:
            section: The IT Act section (e.g., "194C").
            
        Returns:
            Dictionary with rate, threshold, and description, or None if not found.
        """
        return IncomeTaxUtils.TDS_RATES.get(section.upper())

    @staticmethod
    def get_section_description(section: str) -> str:
        """
        Get the description of an Income Tax section.
        """
        details = IncomeTaxUtils.TDS_RATES.get(section.upper())
        return details["description"] if details else "Unknown Section"

    @staticmethod
    def check_cash_limit_violation(amount: float, section: str = "40A(3)") -> Tuple[bool, str]:
        """
        Check if a cash transaction violates specific sections.
        
        Args:
            amount: Transaction amount.
            section: Section to check against ("40A(3)" or "269ST").
            
        Returns:
            Tuple (is_violation, message).
        """
        if section == "40A(3)":
            # Disallowance of expenses > 10,000 in cash
            limit = 10000.0
            if amount > limit:
                return True, f"Cash payment of {amount} exceeds 40A(3) limit of {limit}"
        
        elif section == "269ST":
            # Penalty for receiving > 2 Lakhs in cash
            limit = 200000.0
            if amount >= limit:
                return True, f"Cash receipt of {amount} violates 269ST limit of {limit}"
                
        return False, ""

    @staticmethod
    def get_depreciation_rate(asset_block: str) -> float:
        """
        Get depreciation rate for an asset block.
        
        Args:
            asset_block: Name of the asset block.
            
        Returns:
            Depreciation rate percentage.
        """
        return IncomeTaxUtils.DEPRECIATION_RATES.get(asset_block, 0.0)

    @staticmethod
    def calculate_tds(amount: float, section: str, deductee_type: str = "other") -> float:
        """
        Calculate TDS amount based on section and deductee type.
        
        Args:
            amount: Taxable amount.
            section: TDS section.
            deductee_type: 'individual' or 'other' (company/firm).
            
        Returns:
            Calculated TDS amount.
        """
        details = IncomeTaxUtils.TDS_RATES.get(section.upper())
        if not details:
            return 0.0
            
        rate = 0.0
        if section == "194C":
            rate = details.get("rate_individual") if deductee_type.lower() == "individual" else details.get("rate_other")
        elif section == "194J":
            # Assuming professional for simplicity, logic needs refinement for technical vs professional
            rate = details.get("rate_professional", 10.0)
        else:
            rate = details.get("rate", 0.0)
            
        return round(amount * (rate / 100), 2)
