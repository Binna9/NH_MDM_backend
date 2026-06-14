import logging
import random
import string

from solapi import SolapiMessageService
from solapi.model.request.message import Message as RequestMessage

from app.core.config import get_settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

OTP_KEY_PREFIX = "otp:"
OTP_DIGITS = 6


def _make_key(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())
    return f"{OTP_KEY_PREFIX}{digits}"


def _generate_code() -> str:
    return "".join(random.choices(string.digits, k=OTP_DIGITS))


async def send_otp(phone: str) -> None:
    settings = get_settings()
    code = _generate_code()
    key = _make_key(phone)

    redis = get_redis()
    await redis.set(key, code, ex=settings.otp_ttl_seconds)

    try:
        service = SolapiMessageService(
            api_key=settings.solapi_api_key,
            api_secret=settings.solapi_api_secret,
        )
        service.send(RequestMessage(
            from_=settings.solapi_sender_phone,
            to=phone,
            text=f"[NH MDM] 고양축산농협 조합원 인증번호 [{code}]를 입력해주세요. 감사합니다.",
        ))
    except Exception:
        await redis.delete(key)
        logger.exception("SMS 발송 실패 (phone=%s)", phone)
        raise ValueError("문자 발송에 실패했습니다. 잠시 후 다시 시도해주세요.")


async def verify_otp(phone: str, code: str) -> bool:
    key = _make_key(phone)
    redis = get_redis()
    stored = await redis.get(key)
    if stored is None or stored != code:
        return False
    await redis.delete(key)
    return True
