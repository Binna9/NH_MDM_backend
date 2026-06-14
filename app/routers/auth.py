from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import LoginResponse, MemberLoginRequest, MemberLoginResponse, PartnerLoginRequest
from app.services.member_service import authenticate_member
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


@router.post("/member-login", response_model=MemberLoginResponse)
def member_login(payload: MemberLoginRequest, db: Session = Depends(get_db)) -> MemberLoginResponse:
    try:
        return authenticate_member(
            db,
            nh_member_name=payload.nh_member_name,
            ssn_front=payload.ssn_front,
            ssn_back=payload.ssn_back,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
