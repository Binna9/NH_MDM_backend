from pydantic import BaseModel, Field


class PartnerLoginRequest(BaseModel):
    name: str = Field(min_length=1)
    resident_front: str = Field(min_length=6, max_length=6)
    resident_back: str = Field(min_length=7, max_length=7)


class KakaoLoginRequest(BaseModel):
    authorization_code: str = Field(min_length=1)
    redirect_uri: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    partner_id: str
    partner_name: str
