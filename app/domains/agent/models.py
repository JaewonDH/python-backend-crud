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

그룹1/그룹2는 단일 선택이므로 TB_AGENT 컬럼(GROUP1_CD, GROUP2_CD)으로 직접 관리.
"""
from datetime import datetime

from sqlalchemy import CHAR, Column, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.models.base import Base, generate_uuid


class Agent(Base):
    """TB_AGENT: Agent 카드 (핵심)"""
    __tablename__ = "TB_AGENT"

    agent_id: str = Column("AGENT_ID", String(36), primary_key=True, default=generate_uuid)
    agent_nm: str = Column("AGENT_NM", String(200), nullable=False)
    agent_desc: str | None = Column("AGENT_DESC", Text, nullable=True)
    # 신청 시 입력 필드
    task_no: str | None = Column("TASK_NO", String(100), nullable=True)       # 과제번호
    team_nm: str | None = Column("TEAM_NM", String(200), nullable=True)       # 팀이름
    charge_nm: str | None = Column("CHARGE_NM", String(200), nullable=True)   # 담당
    emp_no: str | None = Column("EMP_NO", String(50), nullable=True)          # 사번
    emp_nm: str | None = Column("EMP_NM", String(100), nullable=True)         # 이름
    # 그룹 단일 선택: TB_CODE_DETAIL에서 1개 선택 (GROUP1_CD / GROUP2_CD 그룹)
    group1_cd: str | None = Column("GROUP1_CD", String(50), nullable=True)    # 그룹1
    group2_cd: str | None = Column("GROUP2_CD", String(50), nullable=True)    # 그룹2
    # 코드 테이블 참조: TB_CODE_DETAIL(AGENT_STATUS_CD)
    # PENDING / REJECTED / DEV / OPEN / DELETE_PENDING
    agent_status_cd: str = Column(
        "AGENT_STATUS_CD", String(20), nullable=False, server_default="PENDING"
    )
    owner_user_id: str = Column("OWNER_USER_ID", String(50), ForeignKey("TB_USER_SYNC.USER_ID"), nullable=False)
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
    agent_id: str = Column("AGENT_ID", String(36), ForeignKey("TB_AGENT.AGENT_ID"), nullable=False)
    user_id: str = Column("USER_ID", String(50), ForeignKey("TB_USER_SYNC.USER_ID"), nullable=False)
    # 코드 테이블 참조: TB_CODE_DETAIL(ROLE_CD) — AGENT_OWNER / AGENT_DEV
    role_cd: str = Column("ROLE_CD", String(20), nullable=False)
    use_yn: str = Column("USE_YN", CHAR(1), nullable=False, server_default="Y")
    reg_dt: datetime = Column("REG_DT", DateTime, nullable=False, server_default=func.sysdate())
    upd_dt: datetime | None = Column("UPD_DT", DateTime, nullable=True)
    reg_user_id: str = Column("REG_USER_ID", String(50), nullable=False)
    upd_user_id: str | None = Column("UPD_USER_ID", String(50), nullable=True)

    agent = relationship("Agent", back_populates="members", foreign_keys="AgentMember.agent_id")
    user = relationship(
        "UserSync",
        back_populates="agent_members",
        primaryjoin="AgentMember.user_id == UserSync.user_id",
        foreign_keys="AgentMember.user_id",
    )


class AgentConsent(Base):
    """
    TB_AGENT_CONSENT: Agent 신청 동의 내역
    consent_item_id 는 common 도메인의 TB_CONSENT_ITEM을 FK로 참조.
    SQLAlchemy 관계는 문자열 "ConsentItem"으로 선언 — 순환 import 없이 해소됨.

    ITEM_TYPE_CD에 따른 처리:
      'YN'   → agree_yn (Y/N) 저장, text_values 없음
      'TEXT' → agree_yn NULL, TB_AGENT_CONSENT_VALUE에 텍스트 입력값 여러 개 저장
    """
    __tablename__ = "TB_AGENT_CONSENT"

    agent_consent_id: str = Column(
        "AGENT_CONSENT_ID", String(36), primary_key=True, default=generate_uuid
    )
    agent_id: str = Column("AGENT_ID", String(36), ForeignKey("TB_AGENT.AGENT_ID"), nullable=False)
    consent_item_id: str = Column("CONSENT_ITEM_ID", String(36), ForeignKey("TB_CONSENT_ITEM.CONSENT_ITEM_ID"), nullable=False)
    # YN 타입만 사용 (TEXT 타입은 NULL)
    agree_yn: str | None = Column("AGREE_YN", CHAR(1), nullable=True)
    agree_dt: datetime = Column("AGREE_DT", Date, nullable=False, server_default=func.sysdate())
    user_id: str = Column("USER_ID", String(50), ForeignKey("TB_USER_SYNC.USER_ID"), nullable=False)

    agent = relationship("Agent", back_populates="consents", foreign_keys="AgentConsent.agent_id")
    # common 도메인 ConsentItem을 문자열 참조 — import 없이 SQLAlchemy가 metadata에서 해소
    consent_item = relationship("ConsentItem", foreign_keys="AgentConsent.consent_item_id")
    # TEXT 타입 입력값 (여러 개)
    text_values = relationship(
        "AgentConsentValue", back_populates="consent", cascade="all, delete-orphan",
        order_by="AgentConsentValue.sort_order",
    )


class AgentConsentValue(Base):
    """
    TB_AGENT_CONSENT_VALUE: TEXT 타입 동의 항목의 사용자 입력값
    하나의 AgentConsent에 여러 개의 텍스트 값을 저장.
    """
    __tablename__ = "TB_AGENT_CONSENT_VALUE"

    consent_value_id: str = Column(
        "CONSENT_VALUE_ID", String(36), primary_key=True, default=generate_uuid
    )
    agent_consent_id: str = Column(
        "AGENT_CONSENT_ID", String(36), ForeignKey("TB_AGENT_CONSENT.AGENT_CONSENT_ID"), nullable=False
    )
    text_value: str = Column("TEXT_VALUE", String(2000), nullable=False)  # 사용자 입력 텍스트
    sort_order: int = Column("SORT_ORDER", Integer, nullable=False)        # 입력 순서
    reg_dt: datetime = Column("REG_DT", DateTime, nullable=False, server_default=func.sysdate())

    consent = relationship("AgentConsent", back_populates="text_values", foreign_keys="AgentConsentValue.agent_consent_id")



class AgentHistory(Base):
    """TB_AGENT_HISTORY: Agent 변경 이력 (전체 보존)"""
    __tablename__ = "TB_AGENT_HISTORY"

    history_id: str = Column(
        "HISTORY_ID", String(36), primary_key=True, default=generate_uuid
    )
    agent_id: str = Column("AGENT_ID", String(36), ForeignKey("TB_AGENT.AGENT_ID"), nullable=False)
    # CHECK 제약: 내부 이력 코드 (앱 Enum 관리)
    # CREATE / UPDATE / STATUS_CHANGE / DELETE_REQ / DELETE
    change_type_cd: str = Column("CHANGE_TYPE_CD", String(30), nullable=False)
    before_status_cd: str | None = Column("BEFORE_STATUS_CD", String(20), nullable=True)
    after_status_cd: str | None = Column("AFTER_STATUS_CD", String(20), nullable=True)
    before_agent_nm: str | None = Column("BEFORE_AGENT_NM", String(200), nullable=True)
    after_agent_nm: str | None = Column("AFTER_AGENT_NM", String(200), nullable=True)
    before_agent_desc: str | None = Column("BEFORE_AGENT_DESC", Text, nullable=True)
    after_agent_desc: str | None = Column("AFTER_AGENT_DESC", Text, nullable=True)
    approval_req_id: str | None = Column("APPROVAL_REQ_ID", String(36), ForeignKey("TB_APPROVAL_REQUEST.APPROVAL_REQ_ID"), nullable=True)
    reg_dt: datetime = Column("REG_DT", DateTime, nullable=False, server_default=func.sysdate())
    reg_user_id: str = Column("REG_USER_ID", String(50), nullable=False)

    agent = relationship("Agent", back_populates="histories", foreign_keys="AgentHistory.agent_id")
    approval_request = relationship(
        "ApprovalRequest",
        back_populates="histories",
        primaryjoin="AgentHistory.approval_req_id == ApprovalRequest.approval_req_id",
        foreign_keys="AgentHistory.approval_req_id",
    )
