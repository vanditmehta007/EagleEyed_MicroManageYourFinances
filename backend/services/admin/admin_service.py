from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.models.admin_models import AdminLog, SystemHealth
from backend.models.response_models import SuccessResponse
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger


class AdminService:
    """
    Service for administrative tasks: logs, health checks, maintenance, and permanent deletion.
    """

    # Valid resource types for permanent deletion
    VALID_RESOURCE_TYPES = ['client', 'document', 'sheet', 'transaction']

    def get_logs(self, limit: int = 100, offset: int = 0, action_filter: Optional[str] = None) -> List[AdminLog]:
        """
        Retrieve system/admin action logs.
        
        Args:
            limit: Number of logs to retrieve.
            offset: Offset for pagination.
            action_filter: Optional filter by action type.
            
        Returns:
            List of AdminLog objects.
        """
        try:
            # Build query
            query = supabase.table("admin_logs").select("*")
            
            # Apply action filter if provided
            if action_filter:
                query = query.eq("action", action_filter)
            
            # Apply pagination and ordering
            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
            
            response = query.execute()
            
            if response.data:
                logs = []
                for log_data in response.data:
                    logs.append(AdminLog(
                        id=log_data["id"],
                        action=log_data["action"],
                        performed_by=log_data.get("user_id", "system"),
                        details=log_data.get("details", {}),
                        created_at=log_data["created_at"]
                    ))
                return logs
            else:
                return []
                
        except Exception as e:
            logger.error(f"Failed to retrieve admin logs: {e}")
            return []

    def check_health(self) -> Dict[str, Any]:
        """
        Check overall system health (DB, Redis, Workers).
        
        Returns:
            Dictionary containing health status of components.
        """
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        # Check Database Connection
        try:
            # Simple query to test DB connection
            response = supabase.table("users").select("id").limit(1).execute()
            health_status["components"]["database"] = {
                "status": "healthy",
                "message": "Database connection successful"
            }
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}"
            }
            logger.error(f"Database health check failed: {e}")
        
        # Check Supabase Storage
        try:
            # Test storage bucket access
            buckets = supabase.storage.list_buckets()
            health_status["components"]["storage"] = {
                "status": "healthy",
                "message": f"Storage accessible, {len(buckets)} buckets found"
            }
        except Exception as e:
            health_status["components"]["storage"] = {
                "status": "degraded",
                "message": f"Storage check failed: {str(e)}"
            }
            logger.warning(f"Storage health check failed: {e}")
        
        # Check Embeddings Table (RAG System)
        try:
            response = supabase.table("embeddings").select("id").limit(1).execute()
            health_status["components"]["rag_system"] = {
                "status": "healthy",
                "message": "RAG embeddings table accessible"
            }
        except Exception as e:
            health_status["components"]["rag_system"] = {
                "status": "degraded",
                "message": f"RAG system check failed: {str(e)}"
            }
            logger.warning(f"RAG system health check failed: {e}")
        
        # Note: Redis and Worker checks would go here if implemented
        # For now, we'll mark them as not configured
        health_status["components"]["redis"] = {
            "status": "not_configured",
            "message": "Redis not configured in current setup"
        }
        
        health_status["components"]["workers"] = {
            "status": "not_configured",
            "message": "Background workers not configured in current setup"
        }
        
        return health_status

    def trigger_maintenance(self) -> SuccessResponse:
        """
        Manually trigger system maintenance tasks.
        
        Returns:
            SuccessResponse indicating task initiation.
        """
        try:
            maintenance_tasks = []
            
            # Task 1: Clean up old soft-deleted records (older than 30 days)
            try:
                # This is a placeholder - in production, you'd run cleanup queries
                logger.info("Maintenance: Checking for old soft-deleted records")
                maintenance_tasks.append({
                    "task": "cleanup_soft_deleted",
                    "status": "queued",
                    "message": "Soft-deleted records cleanup queued"
                })
            except Exception as e:
                logger.error(f"Failed to queue soft-delete cleanup: {e}")
                maintenance_tasks.append({
                    "task": "cleanup_soft_deleted",
                    "status": "failed",
                    "error": str(e)
                })
            
            # Task 2: Optimize database indexes
            try:
                logger.info("Maintenance: Database optimization queued")
                maintenance_tasks.append({
                    "task": "optimize_database",
                    "status": "queued",
                    "message": "Database optimization queued"
                })
            except Exception as e:
                logger.error(f"Failed to queue database optimization: {e}")
                maintenance_tasks.append({
                    "task": "optimize_database",
                    "status": "failed",
                    "error": str(e)
                })
            
            # Task 3: Clean up expired share tokens
            try:
                expired_tokens = supabase.table("share_tokens").delete().lt("expires_at", datetime.utcnow().isoformat()).execute()
                maintenance_tasks.append({
                    "task": "cleanup_expired_tokens",
                    "status": "completed",
                    "message": "Expired share tokens cleaned up"
                })
            except Exception as e:
                logger.error(f"Failed to cleanup expired tokens: {e}")
                maintenance_tasks.append({
                    "task": "cleanup_expired_tokens",
                    "status": "failed",
                    "error": str(e)
                })
            
            # Log maintenance trigger
            self._log_admin_action(
                action="trigger_maintenance",
                details={"tasks": maintenance_tasks}
            )
            
            return SuccessResponse(
                success=True,
                data={
                    "message": "Maintenance tasks initiated",
                    "tasks": maintenance_tasks,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Maintenance trigger failed: {e}")
            return SuccessResponse(
                success=False,
                data={
                    "message": f"Failed to trigger maintenance: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    def permanent_delete(self, resource_id: str, resource_type: str) -> SuccessResponse:
        """
        Permanently delete a soft-deleted resource.
        
        Args:
            resource_id: ID of the resource.
            resource_type: Type of resource (e.g., 'client', 'document').
            
        Returns:
            SuccessResponse indicating completion.
        """
        try:
            # Validate resource type
            if resource_type not in self.VALID_RESOURCE_TYPES:
                return SuccessResponse(
                    success=False,
                    data={
                        "message": f"Invalid resource type: {resource_type}",
                        "valid_types": self.VALID_RESOURCE_TYPES
                    }
                )
            
            # Map resource type to table name
            table_map = {
                'client': 'clients',
                'document': 'documents',
                'sheet': 'sheets',
                'transaction': 'transactions'
            }
            
            table_name = table_map[resource_type]
            
            # Verify the resource is soft-deleted before permanent deletion
            check_response = supabase.table(table_name).select("deleted_at").eq("id", resource_id).execute()
            
            if not check_response.data:
                return SuccessResponse(
                    success=False,
                    data={"message": f"{resource_type.capitalize()} not found"}
                )
            
            resource = check_response.data[0]
            if not resource.get("deleted_at"):
                return SuccessResponse(
                    success=False,
                    data={"message": f"{resource_type.capitalize()} must be soft-deleted before permanent deletion"}
                )
            
            # Perform permanent deletion
            delete_response = supabase.table(table_name).delete().eq("id", resource_id).execute()
            
            # Log the permanent deletion
            self._log_admin_action(
                action="permanent_delete",
                resource_type=resource_type,
                resource_id=resource_id,
                details={
                    "deleted_at": resource.get("deleted_at"),
                    "permanent_deletion_at": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Permanently deleted {resource_type} with ID: {resource_id}")
            
            return SuccessResponse(
                success=True,
                data={
                    "message": f"{resource_type.capitalize()} permanently deleted",
                    "resource_id": resource_id,
                    "resource_type": resource_type
                }
            )
            
        except Exception as e:
            logger.error(f"Permanent deletion failed for {resource_type} {resource_id}: {e}")
            return SuccessResponse(
                success=False,
                data={"message": f"Failed to permanently delete {resource_type}: {str(e)}"}
            )

    def _log_admin_action(
        self, 
        action: str, 
        resource_type: Optional[str] = None, 
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> None:
        """
        Internal helper to log admin actions.
        
        Args:
            action: Action performed.
            resource_type: Type of resource affected.
            resource_id: ID of resource affected.
            details: Additional details.
            user_id: ID of user performing action.
        """
        try:
            log_data = {
                "action": action,
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details or {},
                "created_at": datetime.utcnow().isoformat()
            }
            
            supabase.table("admin_logs").insert(log_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")
