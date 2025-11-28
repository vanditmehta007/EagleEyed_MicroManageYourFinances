from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from fastapi import HTTPException
from backend.models.transaction_models import TransactionCreate, TransactionUpdate, TransactionResponse
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger

class TransactionService:
    """
    Service for managing individual transactions with CRUD, filtering, and bulk operations.
    """

    def create_transaction(self, transaction_data: TransactionCreate) -> TransactionResponse:
        """
        Create a new transaction.
        """
        try:
            transaction_id = str(uuid.uuid4())
            
            new_transaction = {
                "id": transaction_id,
                "sheet_id": transaction_data.sheet_id,
                "date": str(transaction_data.date),
                "description": transaction_data.description,
                "amount": transaction_data.amount,
                "type": transaction_data.type,
                "ledger": transaction_data.ledger or "Uncategorized",
                "vendor": transaction_data.vendor,
                "invoice_number": transaction_data.invoice_number,
                "gstin": transaction_data.gstin,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            data = supabase.table("transactions").insert(new_transaction).execute()
            
            if not data.data:
                raise HTTPException(status_code=500, detail="Failed to create transaction")
            
            return TransactionResponse(**data.data[0])
            
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    def create_bulk_transactions(self, transactions: List[TransactionCreate]) -> Dict[str, Any]:
        """
        Create multiple transactions in a single batch.
        """
        try:
            if not transactions:
                return {"success": True, "count": 0, "message": "No transactions provided"}

            batch_data = []
            now = datetime.utcnow().isoformat()
            
            for txn in transactions:
                batch_data.append({
                    "id": str(uuid.uuid4()),
                    "sheet_id": txn.sheet_id,
                    "date": str(txn.date),
                    "description": txn.description,
                    "amount": txn.amount,
                    "type": txn.type,
                    "ledger": txn.ledger or "Uncategorized",
                    "vendor": txn.vendor,
                    "invoice_number": txn.invoice_number,
                    "gstin": txn.gstin,
                    "created_at": now,
                    "updated_at": now
                })
            
            # Supabase/Postgres bulk insert
            data = supabase.table("transactions").insert(batch_data).execute()
            
            if not data.data:
                 # Depending on Supabase version, insert might return data or not for bulk
                 # If it fails, it usually raises an exception
                 pass

            return {
                "success": True, 
                "count": len(data.data) if data.data else len(batch_data), 
                "message": "Bulk insert successful",
                "data": data.data if data.data else []
            }
            
        except Exception as e:
            logger.error(f"Error in bulk create: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    def get_transaction(self, transaction_id: str) -> TransactionResponse:
        """
        Retrieve a specific transaction by ID.
        """
        try:
            data = supabase.table("transactions").select("*").eq("id", transaction_id).is_("deleted_at", "null").execute()
            
            if not data.data:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            return TransactionResponse(**data.data[0])
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def update_transaction(self, transaction_id: str, update_data: TransactionUpdate) -> TransactionResponse:
        """
        Update a transaction.
        """
        try:
            update_dict = update_data.dict(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow().isoformat()
            
            data = supabase.table("transactions").update(update_dict).eq("id", transaction_id).execute()
            
            if not data.data:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            return TransactionResponse(**data.data[0])
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def delete_transaction(self, transaction_id: str) -> dict:
        """
        Soft delete a transaction.
        """
        try:
            data = supabase.table("transactions").update({
                "deleted_at": datetime.utcnow().isoformat()
            }).eq("id", transaction_id).execute()
            
            if not data.data:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            return {"success": True, "message": "Transaction deleted successfully"}
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def restore_transaction(self, transaction_id: str) -> TransactionResponse:
        """
        Restore a soft-deleted transaction.
        """
        try:
            data = supabase.table("transactions").update({
                "deleted_at": None
            }).eq("id", transaction_id).execute()
            
            if not data.data:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            return TransactionResponse(**data.data[0])
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def list_transactions(
        self,
        sheet_id: Optional[str] = None,
        ledger: Optional[str] = None,
        transaction_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        amount_min: Optional[float] = None,
        amount_max: Optional[float] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TransactionResponse]:
        """
        List transactions with advanced filtering.
        """
        try:
            query = supabase.table("transactions").select("*").is_("deleted_at", "null")
            
            if sheet_id:
                query = query.eq("sheet_id", sheet_id)
            if ledger:
                query = query.eq("ledger", ledger)
            if transaction_type:
                query = query.eq("type", transaction_type)
            if date_from:
                query = query.gte("date", date_from)
            if date_to:
                query = query.lte("date", date_to)
            if amount_min is not None:
                query = query.gte("amount", amount_min)
            if amount_max is not None:
                query = query.lte("amount", amount_max)
            
            # Order by date descending, then created_at
            query = query.order("date", desc=True).order("created_at", desc=True).range(offset, offset + limit - 1)
            
            data = query.execute()
            
            return [TransactionResponse(**txn) for txn in data.data]
            
        except Exception as e:
            logger.error(f"Error listing transactions: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    def get_transactions_by_sheet(self, sheet_id: str) -> List[TransactionResponse]:
        """
        Get all transactions for a specific sheet.
        """
        return self.list_transactions(sheet_id=sheet_id, limit=10000)

    def bulk_update_ledger(self, transaction_ids: List[str], ledger: str) -> dict:
        """
        Bulk update ledger classification for multiple transactions.
        """
        try:
            data = supabase.table("transactions").update({
                "ledger": ledger,
                "updated_at": datetime.utcnow().isoformat()
            }).in_("id", transaction_ids).execute()
            
            return {"success": True, "count": len(data.data)}
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def search_transactions(self, query: str, sheet_id: Optional[str] = None) -> List[TransactionResponse]:
        """
        Search transactions by description or vendor.
        """
        try:
            db_query = supabase.table("transactions").select("*").is_("deleted_at", "null")
            
            if sheet_id:
                db_query = db_query.eq("sheet_id", sheet_id)
            
            # Search in description or vendor
            # Note: 'ilike' syntax in supabase-py might vary slightly depending on version, 
            # but .or_() with raw filter string is standard.
            db_query = db_query.or_(f"description.ilike.%{query}%,vendor.ilike.%{query}%")
            
            data = db_query.execute()
            
            return [TransactionResponse(**txn) for txn in data.data]
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
