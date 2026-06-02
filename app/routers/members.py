from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.member import (
    MemberBulkCreateRequest,
    MemberBulkCreateResponse,
    MemberBulkDeleteRequest,
    MemberBulkDeleteResponse,
    MemberDuplicateCheckResponse,
    MemberExcelUploadResponse,
    MemberExcelValidateResponse,
    MemberItem,
    MemberListResponse,
    MemberUpdateRequest,
)
from app.services.member_excel_service import (
    EXPORT_FILENAME,
    TEMPLATE_FILENAME,
    build_member_excel_export,
    build_member_excel_template,
    upload_member_excel,
    validate_member_excel,
)
from app.services.member_service import (
    check_member_duplicate,
    create_members_batch,
    delete_members_batch,
    search_members,
    update_member,
)
router = APIRouter(prefix="/members", tags=["members"])


@router.get("", response_model=MemberListResponse)
def list_members(
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    nh_member_id: Annotated[str | None, Query(description="조합원 ID (단건 조회)")] = None,
    nh_member_name: Annotated[str | None, Query(description="성명 (부분 일치)")] = None,
    nh_member_ssn: Annotated[str | None, Query(description="실명번호 (완전 일치)")] = None,
    nh_customer_no: Annotated[str | None, Query(description="고객번호 (완전 일치)")] = None,
    nh_member_phone: Annotated[str | None, Query(description="핸드폰 (완전 일치)")] = None,
    is_active: Annotated[str | None, Query(description="유지 여부 (Y/N)")] = None,
) -> MemberListResponse:
    return search_members(
        db,
        page=page,
        size=size,
        nh_member_id=nh_member_id,
        nh_member_name=nh_member_name,
        nh_member_ssn=nh_member_ssn,
        nh_customer_no=nh_customer_no,
        nh_member_phone=nh_member_phone,
        is_active=is_active,
    )


@router.get("/check-duplicate", response_model=MemberDuplicateCheckResponse)
def check_duplicate(
    db: Annotated[Session, Depends(get_db)],
    nh_member_ssn: Annotated[str | None, Query(description="실명번호")] = None,
    nh_customer_no: Annotated[str | None, Query(description="고객번호")] = None,
    nh_member_id: Annotated[str | None, Query(description="수정 시 본인 제외용 조합원 ID")] = None,
) -> MemberDuplicateCheckResponse:
    if nh_member_ssn is None and nh_customer_no is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of nh_member_ssn or nh_customer_no is required",
        )

    return check_member_duplicate(
        db,
        nh_member_ssn=nh_member_ssn,
        nh_customer_no=nh_customer_no,
        exclude_nh_member_id=nh_member_id,
    )


@router.post("", response_model=MemberBulkCreateResponse, status_code=status.HTTP_201_CREATED)
def create_members(
    payload: MemberBulkCreateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> MemberBulkCreateResponse:
    return create_members_batch(db, payload.items)


@router.delete("", response_model=MemberBulkDeleteResponse)
def remove_members(
    payload: MemberBulkDeleteRequest,
    db: Annotated[Session, Depends(get_db)],
) -> MemberBulkDeleteResponse:
    return delete_members_batch(db, payload.nh_member_ids)


@router.get("/excel/download")
def download_members_excel(
    db: Annotated[Session, Depends(get_db)],
    nh_member_name: Annotated[str | None, Query(description="성명 (부분 일치)")] = None,
    nh_member_ssn: Annotated[str | None, Query(description="실명번호 (완전 일치)")] = None,
    nh_customer_no: Annotated[str | None, Query(description="고객번호 (완전 일치)")] = None,
    nh_member_phone: Annotated[str | None, Query(description="핸드폰 (완전 일치)")] = None,
    is_active: Annotated[str | None, Query(description="유지 여부 (Y/N)")] = None,
) -> StreamingResponse:
    content = build_member_excel_export(
        db,
        nh_member_name=nh_member_name,
        nh_member_ssn=nh_member_ssn,
        nh_customer_no=nh_customer_no,
        nh_member_phone=nh_member_phone,
        is_active=is_active,
    )
    headers = {"Content-Disposition": f'attachment; filename="{EXPORT_FILENAME}"'}
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get("/excel/template")
def download_member_excel_template() -> StreamingResponse:
    content = build_member_excel_template()
    headers = {"Content-Disposition": f'attachment; filename="{TEMPLATE_FILENAME}"'}
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.post("/excel/upload", response_model=MemberExcelUploadResponse)
async def upload_members_excel(
    db: Annotated[Session, Depends(get_db)],
    file: Annotated[UploadFile, File(description="조합원 업로드 엑셀 (.xlsx)")],
) -> MemberExcelUploadResponse:
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xlsx files are supported",
        )

    workbook_bytes = await file.read()
    if not workbook_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    try:
        return upload_member_excel(db, workbook_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/excel/validate", response_model=MemberExcelValidateResponse)
async def validate_members_excel(
    db: Annotated[Session, Depends(get_db)],
    file: Annotated[UploadFile, File(description="검증용 조합원 업로드 엑셀 (.xlsx)")],
) -> MemberExcelValidateResponse:
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xlsx files are supported",
        )

    workbook_bytes = await file.read()
    if not workbook_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    try:
        return validate_member_excel(db, workbook_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/{nh_member_id}", response_model=MemberItem)
def patch_member(
    nh_member_id: str,
    payload: MemberUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> MemberItem:
    try:
        member = update_member(db, nh_member_id, payload)
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return MemberItem.model_validate(member)

