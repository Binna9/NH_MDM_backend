from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MemberItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nh_member_id: str
    nh_member_name: str
    nh_member_ssn: str
    nh_customer_no: str
    nh_member_phone: str
    is_active: str


class MemberCreateItem(BaseModel):
    nh_member_name: str = Field(min_length=1, max_length=50)
    nh_member_ssn: str = Field(min_length=1, max_length=8)
    nh_customer_no: str = Field(min_length=1, max_length=10)
    nh_member_phone: str = Field(min_length=1, max_length=13)


class MemberBulkCreateRequest(BaseModel):
    items: list[MemberCreateItem] = Field(min_length=1)


class MemberBulkDeleteRequest(BaseModel):
    nh_member_ids: list[str] = Field(min_length=1)


class MemberBulkError(BaseModel):
    index: int | None = None
    nh_member_id: str | None = None
    message: str


class MemberBulkCreateResponse(BaseModel):
    inserted: int
    failed: int
    items: list[MemberItem]
    errors: list[MemberBulkError]


class MemberBulkDeleteResponse(BaseModel):
    deleted: int
    failed: int
    errors: list[MemberBulkError]


class MemberUpdateRequest(BaseModel):
    nh_member_name: str | None = Field(default=None, min_length=1, max_length=50)
    nh_member_ssn: str | None = Field(default=None, min_length=8, max_length=8)
    nh_customer_no: str | None = Field(default=None, min_length=10, max_length=10)
    nh_member_phone: str | None = Field(default=None, min_length=13, max_length=13)
    is_active: Literal["Y", "N"] | None = None

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> "MemberUpdateRequest":
        if not any(
            value is not None
            for value in (
                self.nh_member_name,
                self.nh_member_ssn,
                self.nh_customer_no,
                self.nh_member_phone,
                self.is_active,
            )
        ):
            raise ValueError("At least one field must be provided")
        return self


class MemberListResponse(BaseModel):
    items: list[MemberItem]
    total: int
    page: int = Field(ge=1)
    size: int = Field(ge=1)
    total_pages: int = Field(ge=0)


class MemberExcelUploadError(BaseModel):
    row: int
    message: str


class MemberExcelUploadResponse(BaseModel):
    inserted: int
    updated: int
    failed: int
    errors: list[MemberExcelUploadError]


class MemberExcelValidateResponse(BaseModel):
    total: int
    would_insert: int
    would_update: int
    failed: int
    errors: list[MemberExcelUploadError]


class MemberDuplicateCheckResponse(BaseModel):
    is_duplicate: bool
    nh_member_ssn_duplicate: bool
    nh_customer_no_duplicate: bool
    matched_by_ssn: MemberItem | None = None
    matched_by_customer_no: MemberItem | None = None
