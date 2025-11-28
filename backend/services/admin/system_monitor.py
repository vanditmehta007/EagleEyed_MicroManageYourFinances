from typing import Dict, Any
from datetime import datetime
import time
from backend.utils.supabase_client import supabase
from backend.utils.logger import logger


class SystemMonitor:
    """
    Service for monitoring system health and status.
    """

    @staticmethod
    def get_basic_health() -> Dict[str, Any]:
        """
        Basic application health check (Liveness probe).
        
        This is a lightweight check to verify the API is running.
        Used by load balancers and orchestrators (e.g., Kubernetes liveness probe).
        
        Returns:
            Dictionary with status and timestamp.
        """
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "api": "up"
            }
        }

    @staticmethod
    def get_detailed_status() -> Dict[str, Any]:
        """
        Detailed system status including DB and Redis connectivity (Readiness probe).
        
        This performs actual connectivity checks to verify the system is ready to serve traffic.
        Used by load balancers and orchestrators (e.g., Kubernetes readiness probe).
        
        Returns:
            Dictionary with detailed component status.
        """
        # Initialize status structure
        status = {
            "status": "healthy",  # Overall status: healthy, degraded, or unhealthy
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "api": "up"  # API is always up if this code is running
            }
        }
        
        # Check Database (Supabase) connectivity
        db_status = SystemMonitor._check_database()
        status["components"]["database"] = db_status
        
        # If database is down, mark overall status as unhealthy
        if db_status["status"] == "down":
            status["status"] = "unhealthy"
        elif db_status["status"] == "degraded":
            status["status"] = "degraded"
        
        # Check Redis connectivity (if configured)
        redis_status = SystemMonitor._check_redis()
        status["components"]["redis"] = redis_status
        
        # Redis is optional, so only degrade status if it's expected to be up
        if redis_status["status"] == "down" and redis_status.get("configured", False):
            if status["status"] == "healthy":
                status["status"] = "degraded"
        
        # Check Storage (Supabase Storage) connectivity
        storage_status = SystemMonitor._check_storage()
        status["components"]["storage"] = storage_status
        
        # Storage issues degrade but don't make system unhealthy
        if storage_status["status"] == "down":
            if status["status"] == "healthy":
                status["status"] = "degraded"
        
        return status

    @staticmethod
    def _check_database() -> Dict[str, Any]:
        """
        Check database connectivity by performing a simple query.
        
        Returns:
            Dictionary with database status, response time, and details.
        """
        try:
            # Record start time for response time measurement
            start_time = time.time()
            
            # Perform a lightweight query to test connection
            # We just check if we can query the users table (should always exist)
            response = supabase.table("users").select("id").limit(1).execute()
            
            # Calculate response time in milliseconds
            response_time_ms = (time.time() - start_time) * 1000
            
            # Check if response time is acceptable (< 1000ms is good, < 3000ms is degraded)
            if response_time_ms < 1000:
                db_status = "up"
            elif response_time_ms < 3000:
                db_status = "degraded"
            else:
                db_status = "slow"
            
            return {
                "status": db_status,
                "response_time_ms": round(response_time_ms, 2),
                "message": "Database connection successful",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Database connection failed
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "down",
                "error": str(e),
                "message": "Database connection failed",
                "timestamp": datetime.utcnow().isoformat()
            }

    @staticmethod
    def _check_redis() -> Dict[str, Any]:
        """
        Check Redis connectivity.
        
        Note: Redis is not currently configured in this application.
        This is a placeholder for future implementation.
        
        Returns:
            Dictionary with Redis status.
        """
        # TODO: Implement actual Redis check when Redis is configured
        # Example implementation:
        # try:
        #     redis_client = redis.Redis(host='localhost', port=6379, db=0)
        #     redis_client.ping()
        #     return {"status": "up", "configured": True}
        # except Exception as e:
        #     return {"status": "down", "configured": True, "error": str(e)}
        
        return {
            "status": "not_configured",
            "configured": False,
            "message": "Redis is not configured in the current setup",
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    def _check_storage() -> Dict[str, Any]:
        """
        Check Supabase Storage connectivity.
        
        Returns:
            Dictionary with storage status.
        """
        try:
            # Record start time
            start_time = time.time()
            
            # Try to list storage buckets as a connectivity test
            buckets = supabase.storage.list_buckets()
            
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            return {
                "status": "up",
                "response_time_ms": round(response_time_ms, 2),
                "buckets_count": len(buckets),
                "message": "Storage connection successful",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Storage connection failed
            logger.error(f"Storage health check failed: {e}")
            return {
                "status": "down",
                "error": str(e),
                "message": "Storage connection failed",
                "timestamp": datetime.utcnow().isoformat()
            }
