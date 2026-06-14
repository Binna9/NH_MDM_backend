from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import (
    LoginResponse,
    MemberLoginRequest,
    MemberLoginResponse,
    OtpSendRequest,
    OtpVerifyRequest,
    OtpVerifyResponse,
    PartnerLoginRequest,
)
from app.services.member_service import authenticate_member
from app.services.otp_service import send_otp, verify_otp
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


@router.post("/otp/send", status_code=status.HTTP_204_NO_CONTENT)
async def otp_send(payload: OtpSendRequest) -> None:
    try:
        await send_otp(payload.phone)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.post("/otp/verify", response_model=OtpVerifyResponse)
async def otp_verify(payload: OtpVerifyRequest) -> OtpVerifyResponse:
    verified = await verify_otp(payload.phone, payload.code)
    return OtpVerifyResponse(verified=verified)
