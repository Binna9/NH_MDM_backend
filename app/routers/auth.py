from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import LoginResponse, PartnerLoginRequest
from app.services.partner_service import authenticate_partner

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/partner-login", response_model=LoginResponse)
def partner_login(payload: PartnerLoginRequest) -> LoginResponse:
    login_response = authenticate_partner(payload)

    if login_response is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid partner credentials",
        )

    return login_response
