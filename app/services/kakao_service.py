import httpx

from app.core.config import get_settings


KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_ME_URL = "https://kapi.kakao.com/v2/user/me"


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

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(KAKAO_USER_ME_URL, headers=headers)
        response.raise_for_status()
        return response.json()
