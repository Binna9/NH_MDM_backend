from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NH MDM API"
    app_env: str = "local"
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:8081,http://localhost:19006"

    kakao_rest_api_key: str = ""
    kakao_redirect_uri: str = ""
    kakao_app_return_url: str = ""
    kakao_client_secret: str = ""

    solapi_api_key: str = ""
    solapi_api_secret: str = ""
    solapi_sender_phone: str = ""

    redis_url: str = "redis://localhost:6379/0"

    otp_ttl_seconds: int = 600  # 10분

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/nh"
    database_schema: str = "nh"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
