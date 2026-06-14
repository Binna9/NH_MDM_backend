import math
import uuid

import jwt
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.nh_member_info import NhMemberInfo
from app.schemas.auth import MemberLoginResponse
from app.schemas.member import (
    MemberBulkCreateResponse,
    MemberBulkDeleteResponse,
    MemberBulkError,
    MemberCreateItem,
    MemberDuplicateCheckResponse,
    MemberItem,
    MemberListResponse,
    MemberUpdateRequest,
)

settings = get_settings()

def authenticate_member(
    db: Session,
    *,
    nh_member_name: str,
    ssn_front: str,
    ssn_back: str,
) -> MemberLoginResponse:
    ssn = f"{ssn_front}-{ssn_back}"

    member_by_name = db.scalar(
        select(NhMemberInfo).where(NhMemberInfo.nh_member_name == nh_member_name.strip())
    )
    if member_by_name is None:
        raise ValueError("등록된 성명이 없습니다")

    member = db.scalar(
        select(NhMemberInfo).where(
            NhMemberInfo.nh_member_name == nh_member_name.strip(),
            NhMemberInfo.nh_member_ssn == ssn,
        )
    )
    if member is None:
        raise ValueError("주민번호를 잘못 입력하셨습니다")

    if member.is_active != "Y":
        raise ValueError("미사용 등록 사용자 입니다")

    payload = {"sub": member.nh_member_id, "name": member.nh_member_name}
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    return MemberLoginResponse(
        access_token=token,
        nh_member_id=member.nh_member_id,
        nh_member_name=member.nh_member_name,
        nh_customer_no=member.nh_customer_no,
        nh_member_ssn=member.nh_member_ssn,
        nh_member_phone=member.nh_member_phone,
        is_active=member.is_active,
    )


def get_member_by_id(db: Session, nh_member_id: str) -> NhMemberInfo | None:
    return db.get(NhMemberInfo, nh_member_id)


def get_member_by_customer_no(db: Session, nh_customer_no: str) -> NhMemberInfo | None:
    return db.scalar(select(NhMemberInfo).where(NhMemberInfo.nh_customer_no == nh_customer_no))


def check_member_duplicate(
    db: Session,
    *,
    nh_member_ssn: str | None = None,
    nh_customer_no: str | None = None,
    exclude_nh_member_id: str | None = None,
) -> MemberDuplicateCheckResponse:
    matched_by_ssn: NhMemberInfo | None = None
    matched_by_customer_no: NhMemberInfo | None = None

    if nh_member_ssn is not None:
        ssn_query = select(NhMemberInfo).where(NhMemberInfo.nh_member_ssn == nh_member_ssn)
        if exclude_nh_member_id is not None:
            ssn_query = ssn_query.where(NhMemberInfo.nh_member_id != exclude_nh_member_id)
        matched_by_ssn = db.scalar(ssn_query)

    if nh_customer_no is not None:
        customer_query = select(NhMemberInfo).where(NhMemberInfo.nh_customer_no == nh_customer_no)
        if exclude_nh_member_id is not None:
            customer_query = customer_query.where(NhMemberInfo.nh_member_id != exclude_nh_member_id)
        matched_by_customer_no = db.scalar(customer_query)

    ssn_duplicate = matched_by_ssn is not None
    customer_duplicate = matched_by_customer_no is not None

    return MemberDuplicateCheckResponse(
        is_duplicate=ssn_duplicate or customer_duplicate,
        nh_member_ssn_duplicate=ssn_duplicate,
        nh_customer_no_duplicate=customer_duplicate,
        matched_by_ssn=MemberItem.model_validate(matched_by_ssn) if matched_by_ssn else None,
        matched_by_customer_no=MemberItem.model_validate(matched_by_customer_no)
        if matched_by_customer_no
        else None,
    )


def search_members(
    db: Session,
    *,
    page: int,
    size: int,
    nh_member_id: str | None = None,
    nh_member_name: str | None = None,
    nh_member_ssn: str | None = None,
    nh_customer_no: str | None = None,
    nh_member_phone: str | None = None,
    is_active: str | None = None,
) -> MemberListResponse:
    query = select(NhMemberInfo)
    count_query = select(func.count()).select_from(NhMemberInfo)

    if nh_member_id is not None:
        query = query.where(NhMemberInfo.nh_member_id == nh_member_id)
        count_query = count_query.where(NhMemberInfo.nh_member_id == nh_member_id)
    if nh_member_name is not None:
        query = query.where(NhMemberInfo.nh_member_name.ilike(f"%{nh_member_name}%"))
        count_query = count_query.where(NhMemberInfo.nh_member_name.ilike(f"%{nh_member_name}%"))
    if nh_member_ssn is not None:
        query = query.where(NhMemberInfo.nh_member_ssn == nh_member_ssn)
        count_query = count_query.where(NhMemberInfo.nh_member_ssn == nh_member_ssn)
    if nh_customer_no is not None:
        query = query.where(NhMemberInfo.nh_customer_no == nh_customer_no)
        count_query = count_query.where(NhMemberInfo.nh_customer_no == nh_customer_no)
    if nh_member_phone is not None:
        query = query.where(NhMemberInfo.nh_member_phone == nh_member_phone)
        count_query = count_query.where(NhMemberInfo.nh_member_phone == nh_member_phone)
    if is_active is not None:
        query = query.where(NhMemberInfo.is_active == is_active)
        count_query = count_query.where(NhMemberInfo.is_active == is_active)

    total = db.scalar(count_query) or 0
    offset = (page - 1) * size
    rows = db.scalars(
        query.order_by(NhMemberInfo.nh_member_name, NhMemberInfo.nh_customer_no).offset(offset).limit(size)
    ).all()

    total_pages = math.ceil(total / size) if total > 0 else 0

    return MemberListResponse(
        items=[MemberItem.model_validate(row) for row in rows],
        total=total,
        page=page,
        size=size,
        total_pages=total_pages,
    )


def update_member(db: Session, nh_member_id: str, payload: MemberUpdateRequest) -> NhMemberInfo:
    member = get_member_by_id(db, nh_member_id)
    if member is None:
        raise LookupError("Member not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Duplicate nh_member_ssn or nh_customer_no") from exc

    db.refresh(member)
    return member


def create_members_batch(db: Session, items: list[MemberCreateItem]) -> MemberBulkCreateResponse:
    inserted_members: list[NhMemberInfo] = []
    errors: list[MemberBulkError] = []

    for index, item in enumerate(items):
        existing = db.scalar(
            select(NhMemberInfo).where(
                or_(
                    NhMemberInfo.nh_member_ssn == item.nh_member_ssn,
                    NhMemberInfo.nh_customer_no == item.nh_customer_no,
                )
            )
        )
        if existing is not None:
            errors.append(
                MemberBulkError(
                    index=index,
                    message="실명번호 또는 고객번호가 이미 존재합니다.",
                )
            )
            continue

        member = NhMemberInfo(
            nh_member_id=str(uuid.uuid4()),
            nh_member_name=item.nh_member_name,
            nh_member_ssn=item.nh_member_ssn,
            nh_customer_no=item.nh_customer_no,
            nh_member_phone=item.nh_member_phone,
            is_active="Y",
        )

        try:
            with db.begin_nested():
                db.add(member)
                db.flush()
        except IntegrityError:
            errors.append(
                MemberBulkError(
                    index=index,
                    message="실명번호 또는 고객번호가 이미 존재합니다.",
                )
            )
            continue

        inserted_members.append(member)

    if inserted_members:
        db.commit()
        for member in inserted_members:
            db.refresh(member)
    else:
        db.rollback()

    return MemberBulkCreateResponse(
        inserted=len(inserted_members),
        failed=len(errors),
        items=[MemberItem.model_validate(member) for member in inserted_members],
        errors=errors,
    )


def delete_members_batch(db: Session, nh_member_ids: list[str]) -> MemberBulkDeleteResponse:
    deleted = 0
    errors: list[MemberBulkError] = []

    for nh_member_id in nh_member_ids:
        member = get_member_by_id(db, nh_member_id)
        if member is None:
            errors.append(
                MemberBulkError(
                    nh_member_id=nh_member_id,
                    message="Member not found",
                )
            )
            continue

        db.delete(member)
        deleted += 1

    if deleted > 0:
        db.commit()
    else:
        db.rollback()

    return MemberBulkDeleteResponse(
        deleted=deleted,
        failed=len(errors),
        errors=errors,
    )
