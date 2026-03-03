"""
SQLAlchemy DeclarativeBase 및 공통 Mixin 정의
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """모든 모델의 기반 클래스"""
    pass


def generate_uuid() -> str:
    """UUID 문자열 생성 (기본값 함수)"""
    return str(uuid.uuid4())


class TimestampMixin:
    """생성일시/수정일시 공통 컬럼 Mixin"""
    reg_dt: datetime = Column(
        DateTime,
        nullable=False,
        server_default=func.sysdate(),
    )
    upd_dt: datetime | None = Column(DateTime, nullable=True)
