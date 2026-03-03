"""
사용자 도메인 모델
- TB_USER_SYNC: 외부 시스템 사용자 동기화
- TB_AGENT_SYSTEM_ACCESS: Agent 시스템 접근 권한
- TB_USER_PERMISSION: Admin 내부 권한
"""
from datetime import datetime

from sqlalchemy import CHAR, Column, Date, DateTime, String, func
from sqlalchemy.orm import relationship

from app.models.base import Base, generate_uuid


class UserSync(Base):
    """TB_USER_SYNC: 외부 시스템 사용자 동기화 테이블"""
    __tablename__ = "TB_USER_SYNC"

    user_id: str = Column("USER_ID", String(50), primary_key=True, nullable=False)
    user_nm: str = Column("USER_NM", String(100), nullable=False)
    email: str = Column("EMAIL", String(200), nullable=False)
    dept_nm: str | None = Column("DEPT_NM", String(200), nullable=True)
    ext_system_id: str = Column("EXT_SYSTEM_ID", String(50), nullable=False)
    # CHECK 제약: 앱 Enum 관리 (PENDING/SUCCESS/FAIL)
    sync_status: str = Column("SYNC_STATUS", String(20), nullable=False, server_default="PENDING")
    sync_dt: datetime | None = Column("SYNC_DT", Date, nullable=True)
    use_yn: str = Column("USE_YN", CHAR(1), nullable=False, server_default="Y")
    reg_dt: datetime = Column("REG_DT", DateTime, nullable=False, server_default=func.sysdate())
    upd_dt: datetime | None = Column("UPD_DT", DateTime, nullable=True)

    # 관계 정의
    system_accesses = relationship("AgentSystemAccess", back_populates="user")
    permissions = relationship("UserPermission", back_populates="user")
    owned_agents = relationship(
        "Agent",
        back_populates="owner",
        foreign_keys="Agent.owner_user_id",
    )
    agent_members = relationship("AgentMember", back_populates="user")


class AgentSystemAccess(Base):
    """TB_AGENT_SYSTEM_ACCESS: Agent 시스템 접근 권한 테이블"""
    __tablename__ = "TB_AGENT_SYSTEM_ACCESS"

    access_id: str = Column("ACCESS_ID", String(36), primary_key=True, default=generate_uuid)
    user_id: str = Column("USER_ID", String(50), nullable=False)
    # CHECK 제약: 이진 플래그
    grant_yn: str = Column("GRANT_YN", CHAR(1), nullable=False, server_default="Y")
    grant_reason: str | None = Column("GRANT_REASON", String(500), nullable=True)
    grant_dt: datetime = Column("GRANT_DT", Date, nullable=False, server_default=func.sysdate())
    expire_dt: datetime | None = Column("EXPIRE_DT", Date, nullable=True)
    sync_dt: datetime | None = Column("SYNC_DT", Date, nullable=True)
    # CHECK 제약: 앱 Enum 관리 (PENDING/SUCCESS/FAIL)
    sync_status: str = Column("SYNC_STATUS", String(20), nullable=False, server_default="PENDING")
    reg_dt: datetime = Column("REG_DT", DateTime, nullable=False, server_default=func.sysdate())
    upd_dt: datetime | None = Column("UPD_DT", DateTime, nullable=True)

    # 관계 정의
    user = relationship("UserSync", back_populates="system_accesses")


class UserPermission(Base):
    """TB_USER_PERMISSION: Admin 내부 권한 테이블 (ADMIN 단일값)"""
    __tablename__ = "TB_USER_PERMISSION"

    user_permission_id: str = Column(
        "USER_PERMISSION_ID", String(36), primary_key=True, default=generate_uuid
    )
    user_id: str = Column("USER_ID", String(50), nullable=False)
    # CHECK 제약: ADMIN 단일값 (코드 테이블 불필요)
    permission_cd: str = Column("PERMISSION_CD", String(20), nullable=False)
    use_yn: str = Column("USE_YN", CHAR(1), nullable=False, server_default="Y")
    reg_dt: datetime = Column("REG_DT", DateTime, nullable=False, server_default=func.sysdate())
    reg_user_id: str = Column("REG_USER_ID", String(50), nullable=False)
    upd_dt: datetime | None = Column("UPD_DT", DateTime, nullable=True)
    upd_user_id: str | None = Column("UPD_USER_ID", String(50), nullable=True)

    # 관계 정의
    user = relationship("UserSync", back_populates="permissions")
