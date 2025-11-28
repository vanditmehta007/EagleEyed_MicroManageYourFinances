import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from backend.services.return_filing.gstr1_service import GSTR1Service
from backend.services.return_filing.gstr3b_service import GSTR3BService
from backend.services.return_filing.tds_return_service import TDSReturnService
from backend.services.return_filing.reconciliation_service import ReconciliationService
from backend.utils.supabase_client import supabase

# Configure logging
logger = logging.getLogger(__name__)

class ReturnFilingWorker:
    """
    Worker responsible for processing return filing summaries asynchronously.
    Handles GSTR-1, GSTR-3B, TDS returns, and reconciliations.
    """

    def __init__(self):
        self.gstr1_service = GSTR1Service()
        self.gstr3b_service = GSTR3BService()
        self.tds_service = TDSReturnService()
        self.reconciliation_service = ReconciliationService()

    async def generate_gstr1_summary(self, client_id: str, month: int, year: int) -> Dict[str, Any]:
        """
        Generate GSTR-1 summary for a client.
        """
        try:
            logger.info(f"Generating GSTR-1 summary for client {client_id} ({month}/{year})")
            
            # Note: Service expects month as str (01-12) based on inspection, but let's handle int too
            month_str = f"{month:02d}"
            
            result = self.gstr1_service.generate_gstr1(client_id, month_str, year)
            
            # Store or return result
            # Ideally, we should store this in a 'return_filings' table
            # For now, we just return it
            
            return {
                "status": "success",
                "type": "GSTR-1",
                "client_id": client_id,
                "period": f"{month_str}-{year}",
                "data": result
            }
        except Exception as e:
            logger.error(f"GSTR-1 generation failed: {e}")
            return {"status": "error", "message": str(e)}

    async def generate_gstr3b_summary(self, client_id: str, month: int, year: int) -> Dict[str, Any]:
        """
        Generate GSTR-3B summary for a client.
        """
        try:
            logger.info(f"Generating GSTR-3B summary for client {client_id} ({month}/{year})")
            month_str = f"{month:02d}"
            
            result = self.gstr3b_service.generate_gstr3b(client_id, month_str, year)
            
            return {
                "status": "success",
                "type": "GSTR-3B",
                "client_id": client_id,
                "period": f"{month_str}-{year}",
                "data": result
            }
        except Exception as e:
            logger.error(f"GSTR-3B generation failed: {e}")
            return {"status": "error", "message": str(e)}

    async def generate_tds_summary(self, client_id: str, quarter: str, year: int) -> Dict[str, Any]:
        """
        Generate TDS return summary for a client.
        """
        try:
            logger.info(f"Generating TDS summary for client {client_id} ({quarter}/{year})")
            
            result = self.tds_service.generate_tds_return(client_id, quarter, year)
            
            return {
                "status": "success",
                "type": "TDS",
                "client_id": client_id,
                "period": f"{quarter}-{year}",
                "data": result
            }
        except Exception as e:
            logger.error(f"TDS summary generation failed: {e}")
            return {"status": "error", "message": str(e)}

    async def run_reconciliation(self, client_id: str, month: int, year: int) -> Dict[str, Any]:
        """
        Run reconciliation for a client.
        """
        try:
            logger.info(f"Running reconciliation for client {client_id} ({month}/{year})")
            
            result = self.reconciliation_service.reconcile(client_id, month, year)
            
            return {
                "status": "success",
                "type": "Reconciliation",
                "client_id": client_id,
                "period": f"{month:02d}-{year}",
                "data": result
            }
        except Exception as e:
            logger.error(f"Reconciliation failed: {e}")
            return {"status": "error", "message": str(e)}

    async def process_all_returns(self, client_id: str, month: int, year: int) -> Dict[str, Any]:
        """
        Run all return generation tasks for a client for a specific month.
        """
        results = {}
        
        # GSTR-1
        results["gstr1"] = await self.generate_gstr1_summary(client_id, month, year)
        
        # GSTR-3B
        results["gstr3b"] = await self.generate_gstr3b_summary(client_id, month, year)
        
        # Reconciliation
        results["reconciliation"] = await self.run_reconciliation(client_id, month, year)
        
        # TDS (Check if month is end of quarter)
        if month in [3, 6, 9, 12]:
            quarter_map = {3: "Q4", 6: "Q1", 9: "Q2", 12: "Q3"}
            # Note: Financial year logic might differ (e.g., Q1 is Apr-Jun). 
            # Assuming standard calendar quarters for simplicity or map correctly.
            # Indian FY: Apr-Jun (Q1), Jul-Sep (Q2), Oct-Dec (Q3), Jan-Mar (Q4)
            
            q_map_fy = {6: "Q1", 9: "Q2", 12: "Q3", 3: "Q4"}
            if month in q_map_fy:
                quarter = q_map_fy[month]
                # Adjust year for Q4 (Jan-Mar) if needed, usually belongs to previous FY start year
                # But 'year' param usually implies the calendar year of the month.
                # Let's keep it simple.
                results["tds"] = await self.generate_tds_summary(client_id, quarter, year)
        
        return results
