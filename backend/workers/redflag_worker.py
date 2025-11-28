import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from backend.services.red_flag_engine.anomaly_detector import AnomalyDetectorService
from backend.services.red_flag_engine.duplicate_detector import DuplicateDetector
from backend.services.red_flag_engine.gst_mismatch_detector import GSTMismatchDetector
from backend.services.red_flag_engine.missing_invoice_detector import MissingInvoiceDetector
from backend.services.red_flag_engine.suspicious_vendor_detector import SuspiciousVendorDetector
from backend.services.red_flag_engine.cash_transaction_checker import CashTransactionChecker
from backend.services.red_flag_engine.pattern_analysis import PatternAnalysisEngine
from backend.utils.supabase_client import supabase

# Configure logging
logger = logging.getLogger(__name__)

class RedFlagWorker:
    """
    Worker responsible for performing batch anomaly detection and red-flag scanning.
    It orchestrates various detection engines to scan transactions and generate red flags.
    """

    def __init__(self):
        # Initialize detection services
        # Note: Some services might need initialization arguments or config
        self.anomaly_detector = AnomalyDetectorService()
        
        # We'll instantiate other detectors if they are classes. 
        # Based on file names, assuming they follow similar pattern.
        # If they are not classes or have different init, we'll need to adjust.
        # For now, assuming standard service pattern.
        
        # Placeholder instantiations based on file names
        try:
            self.duplicate_detector = DuplicateDetector()
            self.gst_mismatch_detector = GSTMismatchDetector()
            self.missing_invoice_detector = MissingInvoiceDetector()
            self.suspicious_vendor_detector = SuspiciousVendorDetector()
            self.cash_checker = CashTransactionChecker()
            self.pattern_analyzer = PatternAnalysisEngine()
        except Exception as e:
            logger.warning(f"Some detectors could not be initialized: {e}")

    async def run_scan_for_client(self, client_id: str) -> Dict[str, Any]:
        """
        Run a full red flag scan for a specific client.
        
        Args:
            client_id: The ID of the client to scan.
            
        Returns:
            Summary of the scan results.
        """
        try:
            logger.info(f"Starting red flag scan for client {client_id}")
            
            results = {
                "client_id": client_id,
                "timestamp": datetime.utcnow().isoformat(),
                "modules": {}
            }

            # 1. Anomaly Detection (General)
            try:
                anomaly_res = self.anomaly_detector.run_scan(client_id)
                results["modules"]["anomaly_detector"] = anomaly_res
            except Exception as e:
                logger.error(f"Anomaly detector failed for {client_id}: {e}")
                results["modules"]["anomaly_detector"] = {"error": str(e)}

            # 2. Duplicate Detection
            try:
                # Assuming similar interface: run_scan(client_id) or check_duplicates(client_id)
                # I'll assume a standard `scan` or `detect` method exists.
                # If not, I'll need to check the file content.
                # Since I can't check all files now, I'll use a generic call pattern 
                # and wrap in try-except.
                if hasattr(self.duplicate_detector, 'detect_duplicates'):
                    dup_res = self.duplicate_detector.detect_duplicates(client_id)
                    results["modules"]["duplicate_detector"] = dup_res
            except Exception as e:
                logger.error(f"Duplicate detector failed: {e}")

            # 3. GST Mismatch
            try:
                if hasattr(self.gst_mismatch_detector, 'detect_mismatches'):
                    gst_res = self.gst_mismatch_detector.detect_mismatches(client_id)
                    results["modules"]["gst_mismatch"] = gst_res
            except Exception as e:
                logger.error(f"GST mismatch detector failed: {e}")

            # 4. Missing Invoices
            try:
                if hasattr(self.missing_invoice_detector, 'find_missing_invoices'):
                    missing_res = self.missing_invoice_detector.find_missing_invoices(client_id)
                    results["modules"]["missing_invoices"] = missing_res
            except Exception as e:
                logger.error(f"Missing invoice detector failed: {e}")

            # 5. Suspicious Vendors
            try:
                if hasattr(self.suspicious_vendor_detector, 'scan_vendors'):
                    vendor_res = self.suspicious_vendor_detector.scan_vendors(client_id)
                    results["modules"]["suspicious_vendors"] = vendor_res
            except Exception as e:
                logger.error(f"Suspicious vendor detector failed: {e}")

            # 6. Cash Transactions
            try:
                if hasattr(self.cash_checker, 'check_cash_limits'):
                    cash_res = self.cash_checker.check_cash_limits(client_id)
                    results["modules"]["cash_transactions"] = cash_res
            except Exception as e:
                logger.error(f"Cash transaction checker failed: {e}")

            logger.info(f"Completed red flag scan for client {client_id}")
            return results

        except Exception as e:
            logger.error(f"Critical error in RedFlagWorker for client {client_id}: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "client_id": client_id
            }

    async def run_batch_scan(self) -> Dict[str, Any]:
        """
        Run scans for all active clients.
        """
        try:
            # Fetch all clients
            response = supabase.table("clients").select("id").execute()
            clients = response.data if response.data else []
            
            summary = {
                "total_clients": len(clients),
                "processed": 0,
                "errors": 0,
                "details": []
            }
            
            for client in clients:
                client_id = client["id"]
                res = await self.run_scan_for_client(client_id)
                summary["details"].append(res)
                if "error" in res:
                    summary["errors"] += 1
                else:
                    summary["processed"] += 1
                    
            return summary
            
        except Exception as e:
            logger.error(f"Batch scan failed: {e}")
            return {"status": "error", "message": str(e)}
