from fastapi import APIRouter, Depends, HTTPException, Request
from backend.models.auth_models import LoginRequest, SignupRequest, AuthToken, RefreshTokenRequest
from backend.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=AuthToken)
async def signup(request: SignupRequest, service: AuthService = Depends()):
    """
    Register a new user (Client or CA).
    """
    return service.signup(request)

@router.post("/login", response_model=AuthToken)
async def login(request: LoginRequest, service: AuthService = Depends()):
    """
    Authenticate user and return JWT access token.
    """
    return service.login(request)

@router.post("/refresh", response_model=AuthToken)
async def refresh_token(request: RefreshTokenRequest, service: AuthService = Depends()):
    """
    Refresh access token using a valid refresh token.
    """
    return service.refresh_token(request)

@router.get("/me")
async def get_current_user(request: Request, service: AuthService = Depends()):
    """
    Get current authenticated user's profile information.
    """
    user_id = request.state.user_id
    return service.get_user_profile(user_id)
