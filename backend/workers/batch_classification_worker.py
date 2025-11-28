import logging
from typing import List, Dict, Any
from backend.services.ledger_classifier.ledger_classifier_service import LedgerClassifierService

# Configure logging
logger = logging.getLogger(__name__)

class BatchClassificationWorker:
    """
    Worker responsible for performing batch ledger classification tasks.
    Delegates the core logic to the LedgerClassifierService.
    """

    def __init__(self):
        self.classifier_service = LedgerClassifierService()

    def process_transaction_batch(self, transaction_ids: List[str]) -> Dict[str, Any]:
        """
        Process a specific batch of transactions identified by their IDs.

        Args:
            transaction_ids: List of transaction IDs to classify.

        Returns:
            Dictionary containing status and results.
        """
        try:
            logger.info(f"Starting batch classification for {len(transaction_ids)} transactions.")
            
            # Delegate to service
            results = self.classifier_service.classify_transactions(transaction_ids)
            
            logger.info(f"Successfully classified {len(results)} transactions.")
            return {
                "status": "success",
                "processed_count": len(results),
                "results": results
            }
        except Exception as e:
            logger.error(f"Error classifying transaction batch: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "transaction_ids": transaction_ids
            }

    def process_sheet_classification(self, client_id: str, sheet_id: str) -> Dict[str, Any]:
        """
        Process classification for all transactions within a specific sheet.

        Args:
            client_id: The ID of the client.
            sheet_id: The ID of the sheet to classify.

        Returns:
            Dictionary containing status and summary statistics.
        """
        try:
            logger.info(f"Starting bulk classification for sheet {sheet_id} (Client: {client_id}).")
            
            # Delegate to service
            summary = self.classifier_service.bulk_classify(client_id, sheet_id)
            
            logger.info(f"Completed bulk classification for sheet {sheet_id}.")
            return {
                "status": "success",
                "summary": summary
            }
        except Exception as e:
            logger.error(f"Error processing sheet classification: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "sheet_id": sheet_id
            }
