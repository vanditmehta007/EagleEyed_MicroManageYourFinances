from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict

class RoleEnforcementMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce Role-Based Access Control (RBAC).
    Checks if the authenticated user has the required role for the requested endpoint.
    """

    # Define role requirements for specific path prefixes or exact paths
    # Format: "path_prefix": ["allowed_role_1", "allowed_role_2"]
    # More specific paths should come first if order matters in logic, 
    # but dictionary lookup is usually direct.
    # Here we use a simple prefix matching strategy.
    
    ROUTE_PERMISSIONS: Dict[str, List[str]] = {
        "/admin": ["super_admin"],
        "/audit": ["super_admin", "ca_auditor"],
        "/reports": ["super_admin", "ca_auditor", "client_viewer"],
        "/upload": ["super_admin", "ca_auditor", "client_uploader"],
        "/settings": ["super_admin", "ca_auditor"],
        "/users": ["super_admin"]
    }

    async def dispatch(self, request: Request, call_next):
        # Skip if user is not authenticated (handled by JWT middleware)
        if not hasattr(request.state, "user"):
            return await call_next(request)

        user_role = request.state.role
        path = request.url.path

        # Super Admin bypass
        if user_role == "super_admin":
            return await call_next(request)

        # Check permissions
        required_roles = self._get_required_roles(path)
        
        if required_roles:
            if user_role not in required_roles:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": f"Role '{user_role}' is not authorized to access this resource."}
                )

        response = await call_next(request)
        return response

    def _get_required_roles(self, path: str) -> List[str]:
        """
        Match the request path against defined route permissions.
        Returns the list of allowed roles or None if no restriction is defined.
        """
        # Check for exact match or prefix match
        # Sort keys by length descending to match most specific paths first
        sorted_prefixes = sorted(self.ROUTE_PERMISSIONS.keys(), key=len, reverse=True)
        
        for prefix in sorted_prefixes:
            if path.startswith(prefix):
                return self.ROUTE_PERMISSIONS[prefix]
        
        return []
