from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException
from backend.models.auth_models import LoginRequest, SignupRequest, AuthToken, RefreshTokenRequest, TokenPayload
from backend.utils.supabase_client import supabase
from backend.config import settings

class AuthService:
    """
    Service for handling authentication logic including login, signup, and token management.
    """
    
    JWT_SECRET = settings.JWT_SECRET_KEY or "your-secret-key-change-in-production"
    JWT_ALGORITHM = settings.JWT_ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_EXPIRATION_MINUTES

    def signup(self, request: SignupRequest) -> AuthToken:
        """
        Registers a new user (Client or CA) and returns an authentication token.
        """
        try:
            # Create user in Supabase Auth
            auth_response = supabase.auth.sign_up({
                "email": request.email,
                "password": request.password,
                "options": {
                    "data": {
                        "full_name": request.name,
                        "role": request.role
                    }
                }
            })
            
            if not auth_response.user:
                raise HTTPException(status_code=400, detail="User registration failed")

            user = auth_response.user
            
            # Use service role key to bypass RLS for initial user creation
            # This ensures we can write to users/clients/cas tables without auth context issues
            from supabase import create_client
            admin_supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

            # Create user record in users table
            user_data = {
                "id": user.id,
                "full_name": request.name,
                "email": request.email,
                "role": request.role,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            admin_supabase.table("users").insert(user_data).execute()

            # If the user is a client, automatically create a client profile
            if request.role == 'client':
                client_data = {
                    "name": request.name, # Use user's name as business name initially
                    "email": request.email,
                    "created_by": user.id,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                admin_supabase.table("clients").insert(client_data).execute()
            
            # If the user is a CA, automatically create a CA profile
            elif request.role == 'ca':
                ca_data = {
                    "id": user.id,
                    "firm_name": request.name, # Use user's name as firm name initially
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                admin_supabase.table("cas").insert(ca_data).execute()

            # Return tokens from Supabase
            if auth_response.session:
                return AuthToken(
                    access_token=auth_response.session.access_token,
                    refresh_token=auth_response.session.refresh_token,
                    token_type="bearer",
                    expires_in=3600
                )
            elif auth_response.user:
                # Email confirmation enabled, session not created yet
                # Return a dummy token or handle gracefully
                # Ideally, we should change the response model to allow a message, but to keep it simple:
                return AuthToken(
                    access_token="pending_confirmation",
                    refresh_token="pending_confirmation",
                    token_type="bearer",
                    expires_in=0
                )
            else:
                raise HTTPException(status_code=400, detail="Session creation failed")

        except Exception as e:
            print(f"Signup Error: {str(e)}") # Log to console
            raise HTTPException(status_code=400, detail=f"Signup failed: {str(e)}")

    def login(self, request: LoginRequest) -> AuthToken:
        """
        Authenticates a user and returns a JWT access token.
        """
        try:
            # Authenticate with Supabase
            auth_response = supabase.auth.sign_in_with_password({
                "email": request.email,
                "password": request.password
            })
            
            if not auth_response.session:
                raise HTTPException(status_code=401, detail="Invalid credentials")

            return AuthToken(
                access_token=auth_response.session.access_token,
                refresh_token=auth_response.session.refresh_token,
                token_type="bearer",
                expires_in=3600
            )

        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid credentials")

    def refresh_token(self, request: RefreshTokenRequest) -> AuthToken:
        """
        Refreshes an access token using a valid refresh token.
        """
        try:
            session = supabase.auth.refresh_session(request.refresh_token)
            
            if not session.session:
                raise HTTPException(status_code=401, detail="Invalid refresh token")

            return AuthToken(
                access_token=session.session.access_token,
                refresh_token=session.session.refresh_token,
                token_type="bearer",
                expires_in=3600
            )
            
        except Exception as e:
            raise HTTPException(status_code=401, detail="Could not refresh token")

    def validate_token(self, token: str) -> dict:
        """
        Validates a JWT access token and returns user info.
        """
        try:
            user_response = supabase.auth.get_user(token)
            
            if not user_response.user:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            user = user_response.user
            
            return {
                "user_id": user.id,
                "email": user.email,
                "role": user.user_metadata.get("role", "client")
            }
            
        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid token")

    def get_user_profile(self, user_id: str) -> dict:
        """
        Get user profile information from the database.
        """
        try:
            # Fetch user from database
            user_response = supabase.table("users").select("*").eq("id", user_id).single().execute()
            
            if not user_response.data:
                raise HTTPException(status_code=404, detail="User not found")
            
            user_data = user_response.data
            
            return {
                "id": user_data["id"],
                "email": user_data["email"],
                "full_name": user_data.get("full_name"),
                "role": user_data.get("role", "client"),
                "phone": user_data.get("phone"),
                "created_at": user_data.get("created_at")
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch user profile: {str(e)}")
