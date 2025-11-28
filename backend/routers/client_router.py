from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List
from backend.models.client_models import ClientCreate, ClientResponse
from backend.services.client_service import ClientService

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.post("/", response_model=ClientResponse)
async def create_client(
    request: Request, 
    client: ClientCreate, 
    service: ClientService = Depends()
):
    """
    Create a new client entity.
    """
    user_id = request.state.user_id
    return service.create_client(client, user_id)

@router.get("/", response_model=List[ClientResponse])
async def get_clients(
    request: Request, 
    service: ClientService = Depends()
):
    """
    Get all clients accessible to the current user.
    """
    user_id = request.state.user_id
    role = request.state.role
    return service.list_clients(user_id, role)

@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: str, service: ClientService = Depends()):
    """
    Get specific client details.
    """
    return service.get_client(client_id)

@router.put("/{client_id}/assign-ca", response_model=ClientResponse)
async def assign_ca(client_id: str, ca_id: str, service: ClientService = Depends()):
    """
    Assign a Chartered Accountant to a client.
    """
    return service.assign_ca(client_id, ca_id)

from pydantic import BaseModel

class AcceptInviteRequest(BaseModel):
    token: str
    client_id: str

@router.post("/accept-invite", response_model=ClientResponse)
async def accept_invite(
    request: Request,
    invite_data: AcceptInviteRequest,
    service: ClientService = Depends()
):
    """
    Accept a client invitation via share token.
    """
    from backend.services.sharing.share_token_service import ShareTokenService
    
    user_id = request.state.user_id
    role = request.state.role
    
    print(f"Accept invite: user_id={user_id}, role={role}, client_id={invite_data.client_id}")
    
    if role != 'ca':
        print(f"Role check failed: expected 'ca', got '{role}'")
        raise HTTPException(status_code=403, detail=f"Only CAs can accept client invites. Your role: {role}")
    
    # Verify the share token
    token_service = ShareTokenService()
    validation_result = token_service.validate_token(invite_data.token)
    
    if not validation_result.get("valid"):
        raise HTTPException(
            status_code=400, 
            detail=validation_result.get("error", "Invalid or expired invitation token")
        )
    
    # Verify the token is for the correct client
    if validation_result.get("resource_id") != invite_data.client_id:
        raise HTTPException(
            status_code=400,
            detail="Token does not match the specified client"
        )
    
    # Verify the token is for a client resource
    if validation_result.get("resource_type") != "client":
        raise HTTPException(
            status_code=400,
            detail="This token is not for a client invitation"
        )
    
    # All validations passed, assign the CA to the client
    return service.assign_ca(invite_data.client_id, user_id)
