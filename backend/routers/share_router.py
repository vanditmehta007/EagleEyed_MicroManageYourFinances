from fastapi import APIRouter, Depends
from backend.models.share_models import ShareTokenModel, ShareTokenCreate
from backend.services.sharing.share_token_service import ShareTokenService
from backend.services.sharing.link_resolver_service import LinkResolverService

router = APIRouter(prefix="/share", tags=["Share"])

@router.post("/create", response_model=ShareTokenModel)
async def create_share_link(
    request: ShareTokenCreate,
    service: ShareTokenService = Depends()
):
    """
    Create a secure shareable link for a resource.
    """
    return service.create_token(request.resource_type, request.resource_id, request.expires_in_hours)

@router.get("/resolve/{token}")
async def resolve_share_link(
    token: str, 
    service: LinkResolverService = Depends()
):
    """
    Validate token and retrieve the shared resource.
    """
    return service.resolve_link(token)
