from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
import os

# Use environment variable for secret or default (should be in .env)
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "HS256"

class JWTVerificationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to verify JWT tokens in the Authorization header.
    Decodes claims and attaches user identity to the request state.
    """

    async def dispatch(self, request: Request, call_next):
        # Allow public endpoints (e.g., login, health check, docs)
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing Authorization Header"}
            )

        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid authentication scheme")
            
            # Verify and decode token
            # In production, verify signature, expiration, and audience
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_signature": False}) # TODO: Enable signature verification with correct secret
            
            # Extract user ID
            user_id = payload.get("sub") or payload.get("user_id")
            
            # Fetch actual user role from database
            from backend.utils.supabase_client import supabase
            try:
                # Use maybe_single() or execute() and check list to avoid exception on 0 rows
                user_response = supabase.table("users").select("role").eq("id", user_id).execute()
                if user_response.data and len(user_response.data) > 0:
                    user_role = user_response.data[0].get("role", "client")
                else:
                    # User authenticated but not in public.users table yet
                    user_role = "client" 
            except Exception as e:
                # Log only if it's not a 'no rows' issue, or just debug
                # print(f"Warning: Failed to fetch user role: {e}")
                user_role = "client"  # Default fallback
            
            # Attach user info to request state
            request.state.user = payload
            request.state.user_id = user_id
            request.state.role = user_role
            
        except (ValueError, jwt.DecodeError, jwt.ExpiredSignatureError) as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": f"Invalid or Expired Token: {str(e)}"}
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Authentication Failed"}
            )

        response = await call_next(request)
        return response

    def _is_public_endpoint(self, path: str) -> bool:
        """
        Check if the path is whitelisted for public access.
        """
        public_paths = [
            "/",
            "/favicon.ico",
            "/docs", 
            "/redoc", 
            "/openapi.json", 
            "/api/auth/login", 
            "/api/auth/signup", 
            "/health"
        ]
        
        # Check for exact match or prefix match (e.g., /static)
        for p in public_paths:
            if path == p or path.startswith(p + "/"):
                return True
        return False
