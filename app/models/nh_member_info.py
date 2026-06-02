from sqlalchemy import String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import get_settings
from app.core.database import Base

settings = get_settings()


class NhMemberInfo(Base):
    __tablename__ = "nh_member_info"
    __table_args__ = {"schema": settings.database_schema}

    nh_member_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        server_default=text("gen_random_uuid()::text"),
    )
    nh_member_name: Mapped[str] = mapped_column(String(50), nullable=False)
    nh_member_ssn: Mapped[str] = mapped_column(String(12), nullable=False, unique=True)
    nh_customer_no: Mapped[str] = mapped_column(String(12), nullable=False, unique=True)
    nh_member_phone: Mapped[str] = mapped_column(String(13), nullable=False)
    is_active: Mapped[str] = mapped_column(String(1), nullable=False, default="Y")
