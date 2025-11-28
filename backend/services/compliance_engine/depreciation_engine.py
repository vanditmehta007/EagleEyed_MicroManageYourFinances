from typing import List, Dict, Any
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger
from datetime import datetime


class DepreciationEngine:
    """
    Service for computing depreciation according to Income‑Tax block‑of‑assets rules
    and for suggesting appropriate year‑end journal entries.
    """

    def calculate_depreciation(self, asset_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Compute depreciation for a list of asset identifiers.

        Args:
            asset_ids: List of asset IDs for which depreciation should be calculated.

        Returns:
            A list of dictionaries (or model instances) containing depreciation details
            such as asset_id, depreciation_amount, depreciation_rate, and applicable
            financial year.
        """
        results = []
        
        if not asset_ids:
            return results
        
        try:
            # For now, treat transactions marked as capital_expense as assets
            # In a full implementation, there would be a separate assets table
            response = supabase.table("transactions").select("*").in_("id", asset_ids).eq("capital_expense", True).execute()
            assets = response.data if response.data else []
            
            # Depreciation rates as per Income Tax Act (block of assets)
            depreciation_rates = {
                "building": 10.0,  # 10% for buildings
                "machinery": 15.0,  # 15% for general machinery
                "computer": 40.0,  # 40% for computers
                "vehicle": 15.0,  # 15% for vehicles
                "furniture": 10.0,  # 10% for furniture
                "default": 15.0  # Default rate
            }
            
            current_year = datetime.now().year
            
            for asset in assets:
                asset_id = asset.get("id", "")
                amount = float(asset.get("amount", 0))
                description = asset.get("description", "").lower()
                
                # Determine asset type from description
                asset_type = "default"
                if any(word in description for word in ["building", "construction", "property"]):
                    asset_type = "building"
                elif any(word in description for word in ["machine", "equipment", "plant"]):
                    asset_type = "machinery"
                elif any(word in description for word in ["computer", "laptop", "server"]):
                    asset_type = "computer"
                elif any(word in description for word in ["vehicle", "car", "truck"]):
                    asset_type = "vehicle"
                elif any(word in description for word in ["furniture", "furnishing"]):
                    asset_type = "furniture"
                
                rate = depreciation_rates.get(asset_type, depreciation_rates["default"])
                depreciation_amount = amount * (rate / 100)
                
                results.append({
                    "asset_id": asset_id,
                    "asset_description": asset.get("description", ""),
                    "asset_type": asset_type,
                    "cost": amount,
                    "depreciation_rate": rate,
                    "depreciation_amount": round(depreciation_amount, 2),
                    "financial_year": current_year,
                    "method": "WDV"  # Written Down Value method
                })
            
        except Exception as e:
            # Return empty results on error
            logger.error(f"Error calculating depreciation: {e}")
            pass
        
        return results

    def suggest_year_end_entries(self, financial_year: int) -> List[Dict[str, Any]]:
        """
        Suggest journal entries required at year‑end to record depreciation.

        Args:
            financial_year: The fiscal year (e.g., 2024) for which entries are needed.

        Returns:
            A list of dictionaries (or model instances) representing suggested journal
            entries, typically including debit and credit accounts, amounts, and
            descriptive notes.
        """
        journal_entries = []
        
        try:
            # TODO: Determine which assets have depreciation to be booked for the given year
            # Fetch all sheets for the given financial year
            sheets_response = supabase.table("sheets").select("id, client_id, name").eq("financial_year", financial_year).is_("deleted_at", "null").execute()
            
            if not sheets_response.data:
                logger.info(f"No sheets found for financial year {financial_year}")
                return journal_entries
            
            sheets = sheets_response.data
            
            # Process each sheet to find capital assets
            for sheet in sheets:
                sheet_id = sheet["id"]
                sheet_name = sheet.get("name", "Unknown Sheet")
                
                # Fetch all capital expense transactions for this sheet
                # These represent assets that need depreciation
                transactions_response = supabase.table("transactions").select("*").eq("sheet_id", sheet_id).eq("capital_expense", True).is_("deleted_at", "null").execute()
                
                if not transactions_response.data:
                    continue
                
                capital_assets = transactions_response.data
                
                # Get asset IDs for depreciation calculation
                asset_ids = [asset["id"] for asset in capital_assets]
                
                # Calculate depreciation for these assets
                depreciation_details = self.calculate_depreciation(asset_ids)
                
                # TODO: Create standard journal entry structures (e.g., Debit Depreciation Expense,
                #       Credit Accumulated Depreciation) for each applicable asset
                
                # Group depreciation by asset type for consolidated entries
                asset_type_totals = {}
                for dep in depreciation_details:
                    asset_type = dep["asset_type"]
                    if asset_type not in asset_type_totals:
                        asset_type_totals[asset_type] = {
                            "total_depreciation": 0,
                            "asset_count": 0,
                            "rate": dep["depreciation_rate"]
                        }
                    asset_type_totals[asset_type]["total_depreciation"] += dep["depreciation_amount"]
                    asset_type_totals[asset_type]["asset_count"] += 1
                
                # Create journal entries for each asset type
                for asset_type, totals in asset_type_totals.items():
                    total_dep = totals["total_depreciation"]
                    asset_count = totals["asset_count"]
                    rate = totals["rate"]
                    
                    # Create a double-entry journal entry
                    # Debit: Depreciation Expense
                    # Credit: Accumulated Depreciation
                    
                    entry = {
                        "sheet_id": sheet_id,
                        "sheet_name": sheet_name,
                        "financial_year": financial_year,
                        "entry_type": "depreciation",
                        "asset_type": asset_type.capitalize(),
                        "asset_count": asset_count,
                        "depreciation_rate": rate,
                        "total_amount": round(total_dep, 2),
                        "entries": [
                            {
                                "account": "Depreciation Expense",
                                "account_type": "Expense",
                                "debit": round(total_dep, 2),
                                "credit": 0,
                                "narration": f"Depreciation on {asset_type} @ {rate}% for FY {financial_year}"
                            },
                            {
                                "account": f"Accumulated Depreciation - {asset_type.capitalize()}",
                                "account_type": "Contra Asset",
                                "debit": 0,
                                "credit": round(total_dep, 2),
                                "narration": f"Accumulated depreciation on {asset_type} for FY {financial_year}"
                            }
                        ],
                        "narration": f"Year-end depreciation entry for {asset_count} {asset_type} asset(s) @ {rate}%",
                        "date": f"{financial_year}-03-31",  # Assuming March 31 year-end
                        "status": "suggested"
                    }
                    
                    journal_entries.append(entry)
            
            # TODO: Return the collection of suggested entries
            logger.info(f"Generated {len(journal_entries)} depreciation journal entries for FY {financial_year}")
            
        except Exception as e:
            logger.error(f"Error generating year-end entries for FY {financial_year}: {e}")
            # Return empty list on error
            pass
        
        return journal_entries
