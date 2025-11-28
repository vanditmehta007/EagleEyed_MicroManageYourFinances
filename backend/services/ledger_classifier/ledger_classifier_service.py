# backend/services/ledger_classifier/ledger_classifier_service.py

from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.models.ledger_models import LedgerClassification
from backend.services.ledger_classifier.ledger_rules_engine import LedgerRulesEngine
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger
from fastapi import HTTPException


class LedgerClassifierService:
    """
    High-level service for AI-powered ledger classification of transactions.
    
    Responsibilities:
    - Classify transactions using AI models and rule-based logic
    - Store classification results in the database
    - Handle CA overrides and manual corrections
    - Maintain classification history and audit logs
    """

    def __init__(self) -> None:
        self.rules_engine = LedgerRulesEngine()
        logger.info("LedgerClassifierService initialized")

    def classify_transactions(self, transaction_ids: List[str]) -> List[LedgerClassification]:
        """
        Trigger AI-based ledger classification for a list of transactions.
        """
        try:
            # Fetch transactions from database
            response = supabase.table("transactions").select("*").in_("id", transaction_ids).execute()
            transactions = response.data
            
            if not transactions:
                logger.warning(f"No transactions found for IDs: {transaction_ids}")
                return []
            
            classifications = []
            
            for txn in transactions:
                # Apply rule-based classification
                predicted_ledger = self.rules_engine.classify_by_rules(txn)
                
                if not predicted_ledger:
                    predicted_ledger = "Uncategorized"
                    confidence = 0.0
                else:
                    confidence = self.rules_engine.get_confidence_score(txn, predicted_ledger)
                
                # Determine compliance flags
                gst_applicable = self.rules_engine.is_gst_applicable(txn)
                tds_applicable = self.rules_engine.is_tds_applicable(txn)
                is_capital = self.rules_engine.is_capital_expense(txn)
                
                # Update transaction in database
                supabase.table("transactions").update({
                    "ledger": predicted_ledger,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", txn["id"]).execute()
                
                # Create classification object
                classification = LedgerClassification(
                    transaction_id=txn["id"],
                    predicted_ledger=predicted_ledger,
                    confidence=confidence,
                    gst_applicable=gst_applicable,
                    tds_applicable=tds_applicable,
                    is_capital_expense=is_capital
                )
                
                classifications.append(classification)
                
                # TODO: Store classification in classification_history table for audit
                # Store classification history for audit trail
                try:
                    classification_log = {
                        "transaction_id": txn["id"],
                        "predicted_ledger": predicted_ledger,
                        "confidence": confidence,
                        "method": "rule_based",
                        "gst_applicable": gst_applicable,
                        "tds_applicable": tds_applicable,
                        "is_capital_expense": is_capital,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    supabase.table("classification_history").insert(classification_log).execute()
                    logger.debug(f"Classification history logged for transaction {txn['id']}")
                except Exception as history_error:
                    # Don't fail classification if history logging fails
                    logger.warning(f"Failed to log classification history: {history_error}")
            
            logger.info(f"Successfully classified {len(classifications)} transactions")
            return classifications
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

    def override_classification(self, transaction_id: str, new_ledger: str, reason: str, user_id: Optional[str] = None) -> LedgerClassification:
        """
        CA override for a specific transaction's ledger classification.
        
        Args:
            transaction_id: ID of the transaction to override
            new_ledger: New ledger account name
            reason: Reason for the override
            user_id: Optional ID of the user making the override
        """
        try:
            # Validate transaction exists
            txn_response = supabase.table("transactions").select("*").eq("id", transaction_id).execute()
            
            if not txn_response.data:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            txn = txn_response.data[0]
            old_ledger = txn.get("ledger", "Uncategorized")
            
            # Update transaction ledger
            supabase.table("transactions").update({
                "ledger": new_ledger,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", transaction_id).execute()
            
            # TODO: Log the override in classification_history table
            # Log the override in classification_history table
            try:
                classification_log = {
                    "transaction_id": transaction_id,
                    "old_ledger": old_ledger,
                    "predicted_ledger": new_ledger,
                    "confidence": 1.0,  # Manual override = 100% confidence
                    "method": "manual_override",
                    "reason": reason,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                supabase.table("classification_history").insert(classification_log).execute()
                logger.info(f"Override logged for transaction {transaction_id}: {old_ledger} -> {new_ledger}")
            except Exception as history_error:
                logger.warning(f"Failed to log override history: {history_error}")
            
            # Return updated classification
            return LedgerClassification(
                transaction_id=transaction_id,
                predicted_ledger=new_ledger,
                confidence=1.0,
                gst_applicable=self.rules_engine.is_gst_applicable(txn),
                tds_applicable=self.rules_engine.is_tds_applicable(txn),
                is_capital_expense=self.rules_engine.is_capital_expense(txn)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Override failed: {e}")
            raise HTTPException(status_code=500, detail=f"Override failed: {str(e)}")

    def get_classification_history(self, transaction_id: str) -> List[Dict[str, Any]]:
        """
        Get the history of classifications and overrides for a transaction.
        
        Args:
            transaction_id: ID of the transaction
            
        Returns:
            List of classification history entries, ordered by timestamp (newest first)
        """
        try:
            # TODO: Query classification_history table
            # Query classification_history table
            response = supabase.table("classification_history").select("*").eq("transaction_id", transaction_id).order("timestamp", desc=True).execute()
            
            if response.data:
                logger.info(f"Retrieved {len(response.data)} history entries for transaction {transaction_id}")
                return response.data
            else:
                logger.debug(f"No classification history found for transaction {transaction_id}")
                return []
            
        except Exception as e:
            logger.error(f"Failed to fetch classification history: {e}")
            # Return empty list instead of raising exception
            return []

    def bulk_classify(self, client_id: str, sheet_id: str) -> Dict[str, Any]:
        """
        Classify all transactions for a specific sheet in bulk.
        
        Args:
            client_id: ID of the client
            sheet_id: ID of the sheet
            
        Returns:
            Dictionary with classification statistics
        """
        try:
            # Fetch all transactions for the sheet
            response = supabase.table("transactions").select("*").eq("sheet_id", sheet_id).is_("deleted_at", "null").execute()
            transactions = response.data
            
            if not transactions:
                logger.warning(f"No transactions found for sheet {sheet_id}")
                return {"total": 0, "high_confidence": 0, "low_confidence": 0, "uncategorized": 0}
            
            # Extract transaction IDs
            transaction_ids = [txn["id"] for txn in transactions]
            
            # Run batch classification
            classifications = self.classify_transactions(transaction_ids)
            
            # Aggregate statistics
            total = len(classifications)
            high_confidence = sum(1 for c in classifications if c.confidence >= 0.75)
            low_confidence = sum(1 for c in classifications if c.confidence < 0.75 and c.predicted_ledger != "Uncategorized")
            uncategorized = sum(1 for c in classifications if c.predicted_ledger == "Uncategorized")
            
            result = {
                "total": total,
                "high_confidence": high_confidence,
                "low_confidence": low_confidence,
                "uncategorized": uncategorized,
                "high_confidence_percentage": round((high_confidence / total * 100) if total > 0 else 0, 2),
                "low_confidence_percentage": round((low_confidence / total * 100) if total > 0 else 0, 2),
                "uncategorized_percentage": round((uncategorized / total * 100) if total > 0 else 0, 2)
            }
            
            logger.info(f"Bulk classification completed for sheet {sheet_id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Bulk classification failed: {e}")
            raise HTTPException(status_code=500, detail=f"Bulk classification failed: {str(e)}")

    def get_classification_suggestions(self, transaction_id: str, top_n: int = 3) -> List[Dict[str, Any]]:
        """
        Get top N ledger suggestions for a transaction.
        
        Args:
            transaction_id: ID of the transaction
            top_n: Number of suggestions to return
            
        Returns:
            List of ledger suggestions with confidence scores
        """
        try:
            # Fetch transaction
            txn_response = supabase.table("transactions").select("*").eq("id", transaction_id).execute()
            
            if not txn_response.data:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            txn = txn_response.data[0]
            
            # Get suggestions from rules engine
            suggestions = self.rules_engine.get_top_suggestions(txn, top_n)
            
            logger.debug(f"Generated {len(suggestions)} suggestions for transaction {transaction_id}")
            return suggestions
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get suggestions: {e}")
            return []

    def retrain_model(self, training_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Retrain the classification model using CA-corrected data.
        
        Args:
            training_data: Optional training data. If not provided, fetches from classification_history.
        """
        # TODO: This would involve:
        # 1. Collecting all manual overrides from classification_history
        # 2. Preparing a training dataset (description -> ledger mapping)
        # 3. Fine-tuning an ML model (e.g., using scikit-learn or a simple neural network)
        # 4. Validating model performance on a test set
        # 5. Deploying the updated model
        
        try:
            # Step 1: Collect training data from manual overrides
            if not training_data:
                logger.info("Collecting training data from classification history...")
                
                # Fetch all manual overrides
                response = supabase.table("classification_history").select("*").eq("method", "manual_override").execute()
                
                if not response.data:
                    return {
                        "status": "no_data",
                        "message": "No manual overrides found for training"
                    }
                
                training_data = response.data
            
            # Step 2: Prepare training dataset
            logger.info(f"Preparing training dataset with {len(training_data)} samples...")
            
            # TODO: Implement actual ML training here
            # For now, update rules engine with learned patterns
            learned_patterns = self._extract_patterns_from_overrides(training_data)
            
            # Step 3: Update rules engine
            if learned_patterns:
                self.rules_engine.update_learned_patterns(learned_patterns)
                logger.info(f"Updated rules engine with {len(learned_patterns)} learned patterns")
            
            return {
                "status": "success",
                "message": f"Model retrained with {len(training_data)} samples",
                "training_samples": len(training_data),
                "learned_patterns": len(learned_patterns),
                "note": "Full ML model training requires ML infrastructure setup"
            }
            
        except Exception as e:
            logger.error(f"Model retraining failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _extract_patterns_from_overrides(self, overrides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract common patterns from manual overrides for rule-based learning.
        
        Args:
            overrides: List of manual override records
            
        Returns:
            List of learned patterns
        """
        patterns = []
        
        # Group overrides by ledger
        ledger_groups = {}
        for override in overrides:
            ledger = override.get("predicted_ledger", "")
            if ledger not in ledger_groups:
                ledger_groups[ledger] = []
            ledger_groups[ledger].append(override)
        
        # Extract common keywords for each ledger
        for ledger, group in ledger_groups.items():
            if len(group) >= 3:  # Only create pattern if we have at least 3 examples
                # This is a simplified pattern extraction
                # In production, use NLP techniques
                patterns.append({
                    "ledger": ledger,
                    "sample_count": len(group),
                    "confidence": min(0.9, 0.5 + (len(group) * 0.05))  # Confidence increases with samples
                })
        
        return patterns

    def get_statistics(self, client_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get classification statistics for a client.
        
        Args:
            client_id: ID of the client
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with classification statistics
        """
        try:
            # Build query
            query = supabase.table("transactions").select("ledger, id").eq("client_id", client_id).is_("deleted_at", "null")
            
            if start_date:
                query = query.gte("date", start_date)
            if end_date:
                query = query.lte("date", end_date)
            
            response = query.execute()
            transactions = response.data
            
            if not transactions:
                return {"total": 0, "by_ledger": {}, "uncategorized_count": 0}
            
            # Aggregate by ledger
            ledger_counts = {}
            uncategorized_count = 0
            
            for txn in transactions:
                ledger = txn.get("ledger", "Uncategorized")
                if ledger == "Uncategorized":
                    uncategorized_count += 1
                ledger_counts[ledger] = ledger_counts.get(ledger, 0) + 1
            
            total = len(transactions)
            
            return {
                "total": total,
                "by_ledger": ledger_counts,
                "uncategorized_count": uncategorized_count,
                "uncategorized_percentage": round((uncategorized_count / total * 100) if total > 0 else 0, 2),
                "unique_ledgers": len(ledger_counts)
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}
