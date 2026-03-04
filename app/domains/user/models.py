"""
사용자 도메인 모델
- TB_USER_SYNC: 외부 시스템 사용자 동기화
- TB_AGENT_SYSTEM_ACCESS: Agent 시스템 접근 권한 (레거시, 인증은 TB_USER_EXT_PERMISSION 사용)
- TB_EXT_PERMISSION: 외부 시스템 권한 마스터 (AGENT_SYSTEM_USER / AGENT_SYSTEM_ADMIN)
- TB_USER_EXT_PERMISSION: 사용자-외부권한 SET 매핑
"""
from datetime import datetime

from sqlalchemy import CHAR, Column, Date, DateTime, ForeignKey, String, func
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
    ext_permissions = relationship("UserExtPermission", back_populates="user")
    owned_agents = relationship(
        "Agent",
        back_populates="owner",
        foreign_keys="Agent.owner_user_id",
    )
    agent_members = relationship("AgentMember", back_populates="user")


class AgentSystemAccess(Base):
    """TB_AGENT_SYSTEM_ACCESS: 레거시 시스템 접근 권한 (인증은 TB_USER_EXT_PERMISSION 사용)"""
    __tablename__ = "TB_AGENT_SYSTEM_ACCESS"

    access_id: str = Column("ACCESS_ID", String(36), primary_key=True, default=generate_uuid)
    user_id: str = Column("USER_ID", String(50), ForeignKey("TB_USER_SYNC.USER_ID"), nullable=False)
    grant_yn: str = Column("GRANT_YN", CHAR(1), nullable=False, server_default="Y")
    grant_reason: str | None = Column("GRANT_REASON", String(500), nullable=True)
    grant_dt: datetime = Column("GRANT_DT", Date, nullable=False, server_default=func.sysdate())
    expire_dt: datetime | None = Column("EXPIRE_DT", Date, nullable=True)
    sync_dt: datetime | None = Column("SYNC_DT", Date, nullable=True)
    sync_status: str = Column("SYNC_STATUS", String(20), nullable=False, server_default="PENDING")
    reg_dt: datetime = Column("REG_DT", DateTime, nullable=False, server_default=func.sysdate())
    upd_dt: datetime | None = Column("UPD_DT", DateTime, nullable=True)


class ExtPermission(Base):
    """TB_EXT_PERMISSION: 외부 시스템 권한 마스터 (AGENT_SYSTEM_USER / AGENT_SYSTEM_ADMIN)"""
    __tablename__ = "TB_EXT_PERMISSION"

    ext_permission_id: str = Column(
        "EXT_PERMISSION_ID", String(36), primary_key=True, default=generate_uuid
    )
    # AGENT_SYSTEM_USER / AGENT_SYSTEM_ADMIN
    permission_cd: str = Column("PERMISSION_CD", String(50), nullable=False, unique=True)
    permission_nm: str = Column("PERMISSION_NM", String(100), nullable=False)
    description: str | None = Column("DESCRIPTION", String(500), nullable=True)
    use_yn: str = Column("USE_YN", CHAR(1), nullable=False, server_default="Y")
    reg_dt: datetime = Column("REG_DT", DateTime, nullable=False, server_default=func.sysdate())

    # 관계 정의
    user_mappings = relationship("UserExtPermission", back_populates="ext_permission")


class UserExtPermission(Base):
    """TB_USER_EXT_PERMISSION: 사용자-외부권한 SET 매핑 테이블"""
    __tablename__ = "TB_USER_EXT_PERMISSION"

    user_ext_permission_id: str = Column(
        "USER_EXT_PERMISSION_ID", String(36), primary_key=True, default=generate_uuid
    )
    user_id: str = Column(
        "USER_ID", String(50), ForeignKey("TB_USER_SYNC.USER_ID"), nullable=False
    )
    ext_permission_id: str = Column(
        "EXT_PERMISSION_ID", String(36), ForeignKey("TB_EXT_PERMISSION.EXT_PERMISSION_ID"), nullable=False
    )
    # 이진 플래그: 권한 활성화 여부
    grant_yn: str = Column("GRANT_YN", CHAR(1), nullable=False, server_default="Y")
    grant_dt: datetime = Column("GRANT_DT", Date, nullable=False, server_default=func.sysdate())
    expire_dt: datetime | None = Column("EXPIRE_DT", Date, nullable=True)
    sync_dt: datetime | None = Column("SYNC_DT", Date, nullable=True)
    reg_dt: datetime = Column("REG_DT", DateTime, nullable=False, server_default=func.sysdate())
    upd_dt: datetime | None = Column("UPD_DT", DateTime, nullable=True)

    # 관계 정의
    user = relationship("UserSync", back_populates="ext_permissions")
    ext_permission = relationship("ExtPermission", back_populates="user_mappings")
