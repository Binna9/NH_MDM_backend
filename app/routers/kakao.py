from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import KakaoLoginRequest
from app.services.kakao_service import exchange_code_for_token, fetch_kakao_profile

router = APIRouter(prefix="/kakao", tags=["kakao"])


@router.post("/login")
async def kakao_login(payload: KakaoLoginRequest) -> dict:
    try:
        access_token = await exchange_code_for_token(
            payload.authorization_code,
            payload.redirect_uri,
        )
        kakao_profile = await fetch_kakao_profile(access_token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to verify Kakao login",
        ) from exc

    return {
        "kakao_id": kakao_profile.get("id"),
        "kakao_account": kakao_profile.get("kakao_account", {}),
    }
