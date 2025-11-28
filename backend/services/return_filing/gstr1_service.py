# backend/services/return_filing/gstr1_service.py

from typing import Dict, Any, List
from datetime import datetime
from collections import defaultdict
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger

class GSTR1Service:
    """
    Service for generating GSTR-1 (outward supplies) return data.
    
    Generates:
    - B2B invoices
    - B2C invoices
    - Export invoices
    - Credit/debit notes
    - HSN summary
    """

    def __init__(self) -> None:
        # TODO: Initialize database connection
        # Supabase client is imported globally
        pass

    def generate_gstr1(self, client_id: str, month: str, year: int) -> Dict[str, Any]:
        """
        Generate GSTR-1 return data for a month.
        
        Args:
            client_id: Client identifier.
            month: Month (01-12).
            year: Year (e.g., 2024).
            
        Returns:
            GSTR-1 data dict in GST portal format.
        """
        try:
            # Calculate date range
            start_date = f"{year}-{month}-01"
            # Simple logic for end of month
            if int(month) == 12:
                next_month = f"{year+1}-01-01"
            else:
                next_month = f"{year}-{int(month)+1:02d}-01"
            
            # TODO: Fetch all outward supply transactions for the period
            # Fetch credit transactions (Sales/Income)
            response = supabase.table("transactions").select("*").eq("client_id", client_id).eq("type", "credit").gte("date", start_date).lt("date", next_month).is_("deleted_at", "null").execute()
            transactions = response.data or []
            
            # TODO: Classify into B2B, B2C, exports
            b2b_txns = [t for t in transactions if t.get("gstin")]
            b2c_txns = [t for t in transactions if not t.get("gstin")]
            
            # TODO: Generate HSN summary
            hsn_summary = self._generate_hsn_summary(transactions)
            
            # TODO: Format according to GST portal JSON schema
            gstr1_data = {
                "gstin": "CLIENT_GSTIN_PLACEHOLDER",  # Should be fetched from client profile
                "fp": f"{month}{year}",  # Financial Period
                "b2b": self._generate_b2b_invoices(b2b_txns),
                "b2cs": self._generate_b2c_invoices(b2c_txns),
                "hsn": {"data": hsn_summary},
                "generated_at": datetime.utcnow().isoformat(),
                "summary": {
                    "total_b2b_count": len(b2b_txns),
                    "total_b2c_count": len(b2c_txns),
                    "total_taxable_value": sum(float(t.get("amount", 0)) for t in transactions)
                }
            }
            
            # TODO: Return GSTR-1 dict
            return gstr1_data
            
        except Exception as e:
            logger.error(f"GSTR-1 generation failed: {e}")
            return {"error": str(e)}

    def _generate_b2b_invoices(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate B2B invoice section.
        
        Args:
            transactions: List of B2B transaction dicts.
            
        Returns:
            List of B2B invoice dicts in GST format.
        """
        # TODO: Filter B2B transactions (with GSTIN)
        # Group by GSTIN (Receiver)
        grouped = defaultdict(list)
        for txn in transactions:
            gstin = txn.get("gstin")
            if gstin:
                grouped[gstin].append(txn)
        
        b2b_list = []
        
        # TODO: Format according to GST schema
        for gstin, txns in grouped.items():
            inv_list = []
            for txn in txns:
                amount = float(txn.get("amount", 0))
                # Assuming 18% GST for simplicity if not specified
                tax_rate = 18.0
                taxable_val = round(amount / (1 + tax_rate/100), 2)
                igst = round(amount - taxable_val, 2)
                
                inv_list.append({
                    "inum": txn.get("invoice_number", "INV001"),
                    "idt": txn.get("date", "").split("T")[0],
                    "val": amount,
                    "pos": gstin[:2],  # State code from GSTIN
                    "rchrg": "N",  # Reverse Charge
                    "inv_typ": "R",  # Regular
                    "itms": [{
                        "num": 1,
                        "itm_det": {
                            "rt": tax_rate,
                            "txval": taxable_val,
                            "iamt": igst,
                            "csamt": 0
                        }
                    }]
                })
            
            b2b_list.append({
                "ctin": gstin,
                "inv": inv_list
            })
            
        # TODO: Return B2B invoice list
        return b2b_list

    def _generate_b2c_invoices(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate B2C invoice section.
        
        Args:
            transactions: List of B2C transaction dicts.
            
        Returns:
            List of B2C invoice dicts in GST format.
        """
        # TODO: Filter B2C transactions (without GSTIN)
        # Group by Place of Supply (State) and Rate
        grouped = defaultdict(float)
        
        for txn in transactions:
            # Default to client's state or generic POS if unknown
            pos = "00"  # Placeholder
            amount = float(txn.get("amount", 0))
            tax_rate = 18.0  # Default
            
            key = (pos, tax_rate)
            grouped[key] += amount
            
        b2cs_list = []
        
        # TODO: Format according to GST schema
        for (pos, rate), total_val in grouped.items():
            taxable_val = round(total_val / (1 + rate/100), 2)
            igst = round(total_val - taxable_val, 2)
            
            b2cs_list.append({
                "sply_ty": "INTRA" if pos == "00" else "INTER", # Simplified logic
                "rt": rate,
                "typ": "OE", # Other E-commerce
                "pos": pos,
                "txval": taxable_val,
                "iamt": igst,
                "csamt": 0
            })
            
        # TODO: Return B2C invoice list
        return b2cs_list

    def _generate_hsn_summary(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate HSN-wise summary.
        
        Args:
            transactions: List of transaction dicts.
            
        Returns:
            List of HSN summary dicts.
        """
        # TODO: Group transactions by HSN code
        hsn_groups = defaultdict(lambda: {"qty": 0, "val": 0.0, "txval": 0.0, "iamt": 0.0})
        
        for txn in transactions:
            hsn = txn.get("hsn_code", "999999")  # Default HSN for services
            amount = float(txn.get("amount", 0))
            tax_rate = 18.0
            taxable = round(amount / (1 + tax_rate/100), 2)
            tax = round(amount - taxable, 2)
            
            hsn_groups[hsn]["qty"] += 1
            hsn_groups[hsn]["val"] += amount
            hsn_groups[hsn]["txval"] += taxable
            hsn_groups[hsn]["iamt"] += tax
            
        # TODO: Calculate totals per HSN
        hsn_list = []
        for hsn, data in hsn_groups.items():
            hsn_list.append({
                "num": len(hsn_list) + 1,
                "hsn_sc": hsn,
                "desc": "Services",  # Placeholder
                "uqc": "OTH",
                "qty": data["qty"],
                "val": round(data["val"], 2),
                "txval": round(data["txval"], 2),
                "iamt": round(data["iamt"], 2),
                "csamt": 0
            })
            
        # TODO: Return HSN summary list
        return hsn_list
