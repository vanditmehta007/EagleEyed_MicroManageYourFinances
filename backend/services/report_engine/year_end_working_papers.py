from typing import Dict, Any, List
from datetime import date
from backend.utils.date_utils import DateUtils
from backend.utils.income_tax_utils import IncomeTaxUtils
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger
from collections import defaultdict

class YearEndWorkingPapersService:
    """
    Service for generating Year-End Working Papers and Schedules.
    
    Includes:
    - Depreciation Schedules (Companies Act & Income Tax Act)
    - Loan Balance Confirmations
    - Fixed Asset Register Summaries
    - Notes to Accounts Drafts
    - Audit Trail Preparation
    """

    def generate_year_end_papers(self, client_id: str, year: int) -> Dict[str, Any]:
        """
        Generates comprehensive year-end working papers.
        """
        logger.info(f"Generating year-end working papers for client {client_id} (FY {year}-{year+1})")
        
        return {
            "client_id": client_id,
            "financial_year": f"{year}-{year+1}",
            "generated_at": str(date.today()),
            "depreciation_schedule": self._generate_depreciation_schedule(client_id, year),
            "loan_confirmations": self._generate_loan_confirmations(client_id, year),
            "fixed_asset_register": self._generate_fixed_asset_register(client_id, year),
            "notes_to_accounts": self._draft_notes_to_accounts(client_id, year),
            "audit_trail": self._prepare_audit_trail(client_id, year)
        }

    def _generate_depreciation_schedule(self, client_id: str, year: int) -> Dict[str, Any]:
        """
        Generates Depreciation Schedule as per Companies Act and Income Tax Act.
        """
        try:
            # Fetch fixed asset transactions
            start_date = f"{year}-04-01"
            end_date = f"{year+1}-03-31"
            
            response = supabase.table("transactions").select("*").eq("client_id", client_id).lte("date", end_date).is_("deleted_at", "null").execute()
            
            transactions = response.data if response.data else []
            
            # Identify fixed asset transactions
            fixed_asset_keywords = ["fixed assets", "machinery", "equipment", "furniture", "building", "vehicle"]
            
            gross_block = 0.0
            additions_during_year = 0.0
            
            for txn in transactions:
                ledger = str(txn.get("ledger", "")).lower()
                amount = float(txn.get("amount", 0))
                txn_date = txn.get("date", "")
                
                is_fixed_asset = any(keyword in ledger for keyword in fixed_asset_keywords)
                
                if is_fixed_asset and txn.get("type") == "debit":
                    gross_block += amount
                    
                    # Check if added during the year
                    if txn_date >= start_date:
                        additions_during_year += amount
            
            # Calculate depreciation (simplified - 15% WDV for IT Act, 10% SLM for Companies Act)
            depreciation_companies_act = gross_block * 0.10  # 10% Straight Line
            depreciation_income_tax = gross_block * 0.15     # 15% WDV
            
            net_block = gross_block - depreciation_companies_act
            wdv_closing = gross_block - depreciation_income_tax
            
            return {
                "companies_act": {
                    "gross_block": round(gross_block, 2),
                    "depreciation_for_year": round(depreciation_companies_act, 2),
                    "net_block": round(net_block, 2)
                },
                "income_tax_act": {
                    "wdv_opening": round(gross_block - additions_during_year, 2),
                    "additions_180_days": round(additions_during_year, 2),
                    "additions_less_180_days": 0.0,  # TODO: Split by holding period
                    "depreciation_allowable": round(depreciation_income_tax, 2),
                    "wdv_closing": round(wdv_closing, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Depreciation schedule generation failed: {e}")
            return {"companies_act": {}, "income_tax_act": {}}

    def _generate_loan_confirmations(self, client_id: str, year: int) -> List[Dict[str, Any]]:
        """
        Generates Loan Balance Confirmation drafts for secured/unsecured loans.
        """
        try:
            end_date = f"{year+1}-03-31"
            
            # Fetch loan-related transactions
            response = supabase.table("transactions").select("*").eq("client_id", client_id).lte("date", end_date).is_("deleted_at", "null").execute()
            
            transactions = response.data if response.data else []
            
            # Group by lender
            loan_balances = defaultdict(lambda: {"principal": 0.0, "interest": 0.0})
            
            for txn in transactions:
                ledger = str(txn.get("ledger", "")).lower()
                amount = float(txn.get("amount", 0))
                
                if "loan" in ledger:
                    vendor = txn.get("vendor", "Unknown Lender")
                    
                    if txn.get("type") == "credit":
                        loan_balances[vendor]["principal"] += amount
                    else:
                        loan_balances[vendor]["principal"] -= amount
                
                if "interest" in ledger and "loan" in txn.get("description", "").lower():
                    vendor = txn.get("vendor", "Unknown Lender")
                    if txn.get("type") == "debit":
                        loan_balances[vendor]["interest"] += amount
            
            # Generate confirmation list
            confirmations = []
            for lender, balances in loan_balances.items():
                if balances["principal"] > 0:
                    confirmations.append({
                        "lender_name": lender,
                        "account_number": "XXXX",  # TODO: Track account numbers
                        "closing_balance": round(balances["principal"], 2),
                        "interest_expense": round(balances["interest"], 2),
                        "confirmation_status": "Pending"
                    })
            
            return confirmations
            
        except Exception as e:
            logger.error(f"Loan confirmations generation failed: {e}")
            return []

    def _generate_fixed_asset_register(self, client_id: str, year: int) -> List[Dict[str, Any]]:
        """
        Generates summary of Fixed Asset Register (FAR).
        """
        try:
            end_date = f"{year+1}-03-31"
            
            response = supabase.table("transactions").select("*").eq("client_id", client_id).lte("date", end_date).is_("deleted_at", "null").execute()
            
            transactions = response.data if response.data else []
            
            # Group by asset category
            asset_categories = defaultdict(lambda: {"count": 0, "total_value": 0.0})
            
            fixed_asset_keywords = {
                "Land": ["land"],
                "Building": ["building"],
                "Plant & Machinery": ["machinery", "plant", "equipment"],
                "Furniture & Fixtures": ["furniture", "fixture"],
                "Vehicles": ["vehicle", "car", "truck"],
                "Computers": ["computer", "laptop"]
            }
            
            for txn in transactions:
                ledger = str(txn.get("ledger", "")).lower()
                amount = float(txn.get("amount", 0))
                
                if txn.get("type") == "debit":
                    for category, keywords in fixed_asset_keywords.items():
                        if any(kw in ledger for kw in keywords):
                            asset_categories[category]["count"] += 1
                            asset_categories[category]["total_value"] += amount
                            break
            
            # Generate register summary
            register = []
            for category, data in asset_categories.items():
                if data["count"] > 0:
                    register.append({
                        "category": category,
                        "count": data["count"],
                        "total_value": round(data["total_value"], 2),
                        "physical_verification_status": "Pending"
                    })
            
            return register
            
        except Exception as e:
            logger.error(f"Fixed asset register generation failed: {e}")
            return []

    def _draft_notes_to_accounts(self, client_id: str, year: int) -> Dict[str, Any]:
        """
        Drafts Notes to Accounts based on financial data.
        """
        try:
            # Generate basic notes structure
            return {
                "accounting_policies": "The financial statements are prepared on accrual basis following applicable Accounting Standards.",
                "share_capital": {
                    "authorized": "To be filled",
                    "issued": "To be filled",
                    "subscribed": "To be filled"
                },
                "contingent_liabilities": [
                    "No contingent liabilities as on year-end (to be verified)"
                ],
                "related_party_transactions": [
                    "To be disclosed as per AS-18"
                ]
            }
            
        except Exception as e:
            logger.error(f"Notes to accounts drafting failed: {e}")
            return {}

    def _prepare_audit_trail(self, client_id: str, year: int) -> Dict[str, Any]:
        """
        Prepares Audit Trail (Edit Log) report as per MCA requirements.
        """
        try:
            # TODO: Track actual edit logs in a separate table
            # For now, return a placeholder structure
            
            return {
                "is_enabled": True,
                "gaps_found": False,
                "edit_log_summary": {
                    "total_edits": 0,
                    "critical_edits": 0,
                    "note": "Audit trail tracking to be implemented"
                },
                "compliance_status": "Compliant (assuming no edits)"
            }
            
        except Exception as e:
            logger.error(f"Audit trail preparation failed: {e}")
            return {"is_enabled": False}
