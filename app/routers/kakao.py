from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.responses import Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.auth import KakaoLoginRequest, MemberLoginResponse
from app.services.kakao_service import complete_kakao_member_login

router = APIRouter(prefix="/kakao", tags=["kakao"])

_CALLBACK_SUCCESS_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>로그인 완료</title>
</head>
<body>
  <p>카카오 로그인이 완료되었습니다. 앱으로 돌아가 주세요.</p>
</body>
</html>"""


def _resolve_redirect_uri(request_redirect_uri: str | None) -> str:
    settings = get_settings()
    redirect_uri = request_redirect_uri or settings.kakao_redirect_uri
    if not redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="redirect_uri is required (request body or KAKAO_REDIRECT_URI env)",
        )
    return redirect_uri


def _callback_error_html(title: str, message: str) -> HTMLResponse:
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
</head>
<body>
  <p>{message}</p>
</body>
</html>"""
    return HTMLResponse(html, status_code=400)


def _redirect_to_app(login_response: MemberLoginResponse) -> RedirectResponse:
    settings = get_settings()
    params = urlencode(
        {
            "access_token": login_response.access_token,
            "nh_member_id": login_response.nh_member_id,
            "nh_member_name": login_response.nh_member_name,
            "nh_customer_no": login_response.nh_customer_no,
            "nh_member_phone": login_response.nh_member_phone,
            "is_active": login_response.is_active,
        }
    )
    separator = "&" if "?" in settings.kakao_app_return_url else "?"
    return RedirectResponse(f"{settings.kakao_app_return_url}{separator}{params}")


@router.get("/callback", response_model=None)
async def kakao_callback(
    db: Annotated[Session, Depends(get_db)],
    code: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
    error_description: Annotated[str | None, Query()] = None,
) -> Response:
    settings = get_settings()
    if not settings.kakao_redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="KAKAO_REDIRECT_URI is not configured",
        )

    if error:
        message = error_description or "카카오 로그인이 취소되었거나 실패했습니다."
        if settings.kakao_app_return_url:
            params = urlencode({"error": error, "error_description": message})
            separator = "&" if "?" in settings.kakao_app_return_url else "?"
            return RedirectResponse(f"{settings.kakao_app_return_url}{separator}{params}")
        return _callback_error_html("로그인 실패", message)

    if not code:
        return _callback_error_html("잘못된 요청", "authorization code가 없습니다.")

    try:
        login_response = await complete_kakao_member_login(
            db,
            authorization_code=code,
            redirect_uri=settings.kakao_redirect_uri,
        )
    except ValueError as exc:
        if settings.kakao_app_return_url:
            params = urlencode({"error": "login_failed", "error_description": str(exc)})
            separator = "&" if "?" in settings.kakao_app_return_url else "?"
            return RedirectResponse(f"{settings.kakao_app_return_url}{separator}{params}")
        return _callback_error_html("로그인 실패", str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to verify Kakao login",
        ) from exc

    if settings.kakao_app_return_url:
        return _redirect_to_app(login_response)

    return HTMLResponse(_CALLBACK_SUCCESS_HTML)


@router.post("/login", response_model=MemberLoginResponse)
async def kakao_login(
    payload: KakaoLoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> MemberLoginResponse:
    redirect_uri = _resolve_redirect_uri(payload.redirect_uri)

    try:
        return await complete_kakao_member_login(
            db,
            authorization_code=payload.authorization_code,
            redirect_uri=redirect_uri,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to verify Kakao login",
        ) from exc
