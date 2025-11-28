from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
from backend.models.recycle_bin_models import RecycleBinItem
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger

class RecycleBinService:
    """
    Service for managing soft-deleted items (Recycle Bin).
    
    Handles:
    - Soft deletion (moving to bin)
    - Restoration
    - Permanent deletion
    - Auto-cleanup of expired items (30 days)
    """

    def __init__(self):
        self.retention_days = 30

    def soft_delete_item(
        self, 
        table_name: str, 
        item_id: str, 
        deleted_by_id: str, 
        deleted_by_role: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Soft delete an item: Mark as deleted in original table and add to recycle bin.
        """
        try:
            current_time = datetime.utcnow()
            expires_at = current_time + timedelta(days=self.retention_days)
            
            # 1. Mark as deleted in original table
            # We assume the table has a 'deleted_at' column
            update_response = supabase.table(table_name).update({"deleted_at": current_time.isoformat()}).eq("id", item_id).execute()
            
            if not update_response.data:
                return {"success": False, "error": "Item not found or already deleted"}
            
            # 2. Add to recycle_bin table
            bin_entry = {
                "id": str(uuid.uuid4()),
                "original_table": table_name,
                "original_id": item_id,
                "deleted_by_id": deleted_by_id,
                "deleted_by_role": deleted_by_role,
                "deleted_at": current_time.isoformat(),
                "expires_at": expires_at.isoformat(),
                "item_metadata": metadata or {}
            }
            
            bin_response = supabase.table("recycle_bin").insert(bin_entry).execute()
            
            if bin_response.data:
                return {"success": True, "message": "Item moved to recycle bin", "bin_id": bin_entry["id"]}
            else:
                # Rollback: Un-delete if bin insert fails (simplified)
                supabase.table(table_name).update({"deleted_at": None}).eq("id", item_id).execute()
                return {"success": False, "error": "Failed to create recycle bin entry"}
                
        except Exception as e:
            logger.error(f"Soft delete failed: {e}")
            return {"success": False, "error": str(e)}

    def restore_item(self, bin_id: str) -> Dict[str, Any]:
        """
        Restore an item from the recycle bin.
        """
        try:
            # 1. Get bin entry
            bin_response = supabase.table("recycle_bin").select("*").eq("id", bin_id).single().execute()
            if not bin_response.data:
                return {"success": False, "error": "Recycle bin item not found"}
            
            item = bin_response.data
            table_name = item["original_table"]
            original_id = item["original_id"]
            
            # 2. Un-delete in original table
            restore_response = supabase.table(table_name).update({"deleted_at": None}).eq("id", original_id).execute()
            
            if not restore_response.data:
                return {"success": False, "error": "Original item not found"}
            
            # 3. Remove from recycle bin
            supabase.table("recycle_bin").delete().eq("id", bin_id).execute()
            
            return {"success": True, "message": "Item restored successfully"}
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return {"success": False, "error": str(e)}

    def permanent_delete_item(self, bin_id: str) -> Dict[str, Any]:
        """
        Permanently delete an item (from original table and recycle bin).
        """
        try:
            # 1. Get bin entry
            bin_response = supabase.table("recycle_bin").select("*").eq("id", bin_id).single().execute()
            if not bin_response.data:
                return {"success": False, "error": "Recycle bin item not found"}
            
            item = bin_response.data
            table_name = item["original_table"]
            original_id = item["original_id"]
            
            # 2. Delete from original table
            # Note: This is a HARD delete
            del_response = supabase.table(table_name).delete().eq("id", original_id).execute()
            
            # 3. Delete from recycle bin
            supabase.table("recycle_bin").delete().eq("id", bin_id).execute()
            
            return {"success": True, "message": "Item permanently deleted"}
            
        except Exception as e:
            logger.error(f"Permanent delete failed: {e}")
            return {"success": False, "error": str(e)}

    def list_deleted_items(self, user_id: str, role: str) -> List[Dict[str, Any]]:
        """
        List deleted items visible to the user.
        """
        try:
            query = supabase.table("recycle_bin").select("*")
            
            # Filter based on who deleted it
            # "found by matching the id of client or ca or admin (the deleting entity)"
            if role != "admin":
                 query = query.eq("deleted_by_id", user_id)
            
            # Admins might see everything, or we can enforce they only see what they deleted too.
            # The requirement says "matching the id of ... admin".
            # If Admin deletes something, Admin ID is stored.
            # If Client deletes something, Client ID is stored.
            # So filtering by `deleted_by_id` seems correct for all roles based on the prompt.
            # However, usually Admins want to see all. But I'll stick to the prompt's implication.
            # Actually, "matching the id of client or ca or admin" implies strict ownership of the deletion action.
            
            if role == "admin":
                # Optional: Allow admin to see all if needed, but prompt implies matching ID.
                # Let's assume Admin sees ALL for supervision, but standard users see theirs.
                # Re-reading: "found by matching the id of client or ca or admin (the deleting entity)"
                # This applies to finding the items. So if I am Admin, I find items where deleted_by_id = MyID.
                # Wait, if Admin deletes a user, does the Admin want to see it? Yes.
                # If Client deletes a doc, Client wants to see it.
                # So `eq("deleted_by_id", user_id)` is the safest interpretation.
                pass
            
            query = query.eq("deleted_by_id", user_id)
            
            response = query.order("deleted_at", desc=True).execute()
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"List deleted items failed: {e}")
            return []

    def cleanup_expired_items(self) -> Dict[str, Any]:
        """
        Auto-cleanup items that have expired (older than 30 days).
        Should be called by a scheduled job (cron).
        """
        try:
            current_time = datetime.utcnow().isoformat()
            
            # 1. Find expired items
            response = supabase.table("recycle_bin").select("*").lt("expires_at", current_time).execute()
            expired_items = response.data if response.data else []
            
            deleted_count = 0
            errors = 0
            
            for item in expired_items:
                res = self.permanent_delete_item(item["id"])
                if res["success"]:
                    deleted_count += 1
                else:
                    errors += 1
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "errors": errors,
                "message": f"Cleaned up {deleted_count} expired items"
            }
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {"success": False, "error": str(e)}
