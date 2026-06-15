import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.auth import MemberLoginResponse
from app.services.member_service import authenticate_member_by_kakao


KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_ME_URL = "https://kapi.kakao.com/v2/user/me"
KAKAO_PROFILE_PROPERTY_KEYS = (
    '["kakao_account.name","kakao_account.birthyear","kakao_account.birthday"]'
)


async def exchange_code_for_token(authorization_code: str, redirect_uri: str) -> str:
    settings = get_settings()

    data = {
        "grant_type": "authorization_code",
        "client_id": settings.kakao_rest_api_key,
        "redirect_uri": redirect_uri,
        "code": authorization_code,
    }

    if settings.kakao_client_secret:
        data["client_secret"] = settings.kakao_client_secret

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(KAKAO_TOKEN_URL, data=data)
        response.raise_for_status()
        token_payload = response.json()

    return token_payload["access_token"]


async def fetch_kakao_profile(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"property_keys": KAKAO_PROFILE_PROPERTY_KEYS}

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(KAKAO_USER_ME_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()


def extract_kakao_identity(kakao_profile: dict) -> tuple[str, str]:
    kakao_account = kakao_profile.get("kakao_account") or {}
    name = kakao_account.get("name")
    birthyear = kakao_account.get("birthyear")
    birthday = kakao_account.get("birthday")

    if not name or not birthyear or not birthday:
        raise ValueError("카카오 인증 정보(성명·생년월일)가 부족합니다")

    if len(birthyear) != 4 or len(birthday) != 4 or not birthday.isdigit():
        raise ValueError("카카오 생년월일 형식이 올바르지 않습니다")

    ssn_front = f"{birthyear[-2:]}{birthday}"
    return name.strip(), ssn_front


async def complete_kakao_member_login(
    db: Session,
    authorization_code: str,
    redirect_uri: str,
) -> MemberLoginResponse:
    access_token = await exchange_code_for_token(authorization_code, redirect_uri)
    kakao_profile = await fetch_kakao_profile(access_token)
    nh_member_name, ssn_front = extract_kakao_identity(kakao_profile)
    return authenticate_member_by_kakao(
        db,
        nh_member_name=nh_member_name,
        ssn_front=ssn_front,
    )
