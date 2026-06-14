from pydantic import BaseModel, Field


class PartnerLoginRequest(BaseModel):
    name: str = Field(min_length=1)
    resident_front: str = Field(min_length=6, max_length=6)
    resident_back: str = Field(min_length=7, max_length=7)


class MemberLoginRequest(BaseModel):
    nh_member_name: str = Field(min_length=1, max_length=50)
    ssn_front: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    ssn_back: str = Field(min_length=1, max_length=1, pattern=r"^\d$")


class KakaoLoginRequest(BaseModel):
    authorization_code: str = Field(min_length=1)
    redirect_uri: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    partner_id: str
    partner_name: str


class MemberLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    nh_member_id: str
    nh_member_name: str
    nh_customer_no: str
    nh_member_ssn: str
    nh_member_phone: str
    is_active: str


class OtpSendRequest(BaseModel):
    phone: str = Field(min_length=1)


class OtpVerifyRequest(BaseModel):
    phone: str = Field(min_length=1)
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class OtpVerifyResponse(BaseModel):
    verified: bool
