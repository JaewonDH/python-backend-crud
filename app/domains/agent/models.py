"""
Agent 도메인 모델
- TB_AGENT: Agent 카드 (핵심)
- TB_AGENT_MEMBER: Agent 구성원 권한 (Owner/Dev)
- TB_AGENT_CONSENT: Agent 신청 동의 내역
- TB_AGENT_HISTORY: Agent 변경 이력

[경계 수정]
ConsentItem 모델이 common 도메인으로 이전되었음.
AgentConsent.consent_item_id 는 FK(VARCHAR2)만 보유하며,
SQLAlchemy 관계는 문자열 참조("ConsentItem")로 선언 — 동일 Base.metadata에서 해소됨.
"""
from datetime import datetime

from sqlalchemy import CHAR, Column, Date, DateTime, String, Text, func
from sqlalchemy.orm import relationship

from app.models.base import Base, generate_uuid


class Agent(Base):
    """TB_AGENT: Agent 카드 (핵심)"""
    __tablename__ = "TB_AGENT"

    agent_id: str = Column("AGENT_ID", String(36), primary_key=True, default=generate_uuid)
    agent_nm: str = Column("AGENT_NM", String(200), nullable=False)
    agent_desc: str | None = Column("AGENT_DESC", Text, nullable=True)
    # 코드 테이블 참조: TB_CODE_DETAIL(AGENT_STATUS_CD)
    # PENDING / REJECTED / DEV / OPEN / DELETE_PENDING
    agent_status_cd: str = Column(
        "AGENT_STATUS_CD", String(20), nullable=False, server_default="PENDING"
    )
    owner_user_id: str = Column("OWNER_USER_ID", String(50), nullable=False)
    # CHECK 제약: 이진 플래그 (소프트 삭제)
    del_yn: str = Column("DEL_YN", CHAR(1), nullable=False, server_default="N")
    del_dt: datetime | None = Column("DEL_DT", Date, nullable=True)
    del_user_id: str | None = Column("DEL_USER_ID", String(50), nullable=True)
    reg_dt: datetime = Column("REG_DT", DateTime, nullable=False, server_default=func.sysdate())
    upd_dt: datetime | None = Column("UPD_DT", DateTime, nullable=True)
    reg_user_id: str = Column("REG_USER_ID", String(50), nullable=False)
    upd_user_id: str | None = Column("UPD_USER_ID", String(50), nullable=True)

    # 관계 정의
    owner = relationship(
        "UserSync",
        back_populates="owned_agents",
        foreign_keys="Agent.owner_user_id",
        primaryjoin="Agent.owner_user_id == UserSync.user_id",
    )
    members = relationship("AgentMember", back_populates="agent", cascade="all, delete-orphan")
    consents = relationship("AgentConsent", back_populates="agent", cascade="all, delete-orphan")
    approval_requests = relationship("ApprovalRequest", back_populates="agent")
    histories = relationship("AgentHistory", back_populates="agent")


class AgentMember(Base):
    """TB_AGENT_MEMBER: Agent 구성원 권한 (Owner/Dev)"""
    __tablename__ = "TB_AGENT_MEMBER"

    agent_member_id: str = Column(
        "AGENT_MEMBER_ID", String(36), primary_key=True, default=generate_uuid
    )
    agent_id: str = Column("AGENT_ID", String(36), nullable=False)
    user_id: str = Column("USER_ID", String(50), nullable=False)
    # 코드 테이블 참조: TB_CODE_DETAIL(ROLE_CD) — AGENT_OWNER / AGENT_DEV
    role_cd: str = Column("ROLE_CD", String(20), nullable=False)
    use_yn: str = Column("USE_YN", CHAR(1), nullable=False, server_default="Y")
    reg_dt: datetime = Column("REG_DT", DateTime, nullable=False, server_default=func.sysdate())
    upd_dt: datetime | None = Column("UPD_DT", DateTime, nullable=True)
    reg_user_id: str = Column("REG_USER_ID", String(50), nullable=False)
    upd_user_id: str | None = Column("UPD_USER_ID", String(50), nullable=True)

    agent = relationship("Agent", back_populates="members")
    user = relationship(
        "UserSync",
        back_populates="agent_members",
        primaryjoin="AgentMember.user_id == UserSync.user_id",
    )


class AgentConsent(Base):
    """
    TB_AGENT_CONSENT: Agent 신청 동의 내역
    consent_item_id 는 common 도메인의 TB_CONSENT_ITEM을 FK로 참조.
    SQLAlchemy 관계는 문자열 "ConsentItem"으로 선언 — 순환 import 없이 해소됨.
    """
    __tablename__ = "TB_AGENT_CONSENT"

    agent_consent_id: str = Column(
        "AGENT_CONSENT_ID", String(36), primary_key=True, default=generate_uuid
    )
    agent_id: str = Column("AGENT_ID", String(36), nullable=False)
    consent_item_id: str = Column("CONSENT_ITEM_ID", String(36), nullable=False)
    # CHECK 제약: 이진 플래그
    agree_yn: str = Column("AGREE_YN", CHAR(1), nullable=False)
    agree_dt: datetime = Column("AGREE_DT", Date, nullable=False, server_default=func.sysdate())
    user_id: str = Column("USER_ID", String(50), nullable=False)

    agent = relationship("Agent", back_populates="consents")
    # common 도메인 ConsentItem을 문자열 참조 — import 없이 SQLAlchemy가 metadata에서 해소
    consent_item = relationship("ConsentItem")


class AgentHistory(Base):
    """TB_AGENT_HISTORY: Agent 변경 이력 (전체 보존)"""
    __tablename__ = "TB_AGENT_HISTORY"

    history_id: str = Column(
        "HISTORY_ID", String(36), primary_key=True, default=generate_uuid
    )
    agent_id: str = Column("AGENT_ID", String(36), nullable=False)
    # CHECK 제약: 내부 이력 코드 (앱 Enum 관리)
    # CREATE / UPDATE / STATUS_CHANGE / DELETE_REQ / DELETE
    change_type_cd: str = Column("CHANGE_TYPE_CD", String(30), nullable=False)
    before_status_cd: str | None = Column("BEFORE_STATUS_CD", String(20), nullable=True)
    after_status_cd: str | None = Column("AFTER_STATUS_CD", String(20), nullable=True)
    before_agent_nm: str | None = Column("BEFORE_AGENT_NM", String(200), nullable=True)
    after_agent_nm: str | None = Column("AFTER_AGENT_NM", String(200), nullable=True)
    before_agent_desc: str | None = Column("BEFORE_AGENT_DESC", Text, nullable=True)
    after_agent_desc: str | None = Column("AFTER_AGENT_DESC", Text, nullable=True)
    approval_req_id: str | None = Column("APPROVAL_REQ_ID", String(36), nullable=True)
    reg_dt: datetime = Column("REG_DT", DateTime, nullable=False, server_default=func.sysdate())
    reg_user_id: str = Column("REG_USER_ID", String(50), nullable=False)

    agent = relationship("Agent", back_populates="histories")
    approval_request = relationship(
        "ApprovalRequest",
        back_populates="histories",
        primaryjoin="AgentHistory.approval_req_id == ApprovalRequest.approval_req_id",
    )
