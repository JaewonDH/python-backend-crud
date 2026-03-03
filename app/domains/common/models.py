"""
공통 코드 도메인 모델
- TB_CODE_GROUP: 공통 코드 그룹 마스터
- TB_CODE_DETAIL: 공통 코드 상세
- TB_CONSENT_ITEM: 개인정보 동의 항목 마스터 ← agent 도메인에서 이전 (경계 수정)

[경계 결정 근거]
ConsentItem은 Agent 신청 시 참조하는 마스터 데이터로,
Agent 비즈니스 로직에 종속되지 않는 공통 참조 데이터임.
CodeGroup/CodeDetail과 동일하게 common 도메인이 소유권을 가짐.
agent 도메인은 TB_AGENT_CONSENT를 통해 consent_item_id(FK)만 참조.
"""
from datetime import datetime

from sqlalchemy import CHAR, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.models.base import Base, generate_uuid


class CodeGroup(Base):
    """TB_CODE_GROUP: 공통 코드 그룹 마스터"""
    __tablename__ = "TB_CODE_GROUP"

    group_cd: str = Column("GROUP_CD", String(50), primary_key=True, nullable=False)
    group_nm: str = Column("GROUP_NM", String(100), nullable=False)
    group_desc: str | None = Column("GROUP_DESC", String(500), nullable=True)
    use_yn: str = Column("USE_YN", CHAR(1), nullable=False, server_default="Y")
    reg_dt: datetime = Column("REG_DT", DateTime, nullable=False, server_default=func.sysdate())
    reg_user_id: str = Column("REG_USER_ID", String(50), nullable=False)
    upd_dt: datetime | None = Column("UPD_DT", DateTime, nullable=True)
    upd_user_id: str | None = Column("UPD_USER_ID", String(50), nullable=True)

    details = relationship("CodeDetail", back_populates="group", cascade="all, delete-orphan")


class CodeDetail(Base):
    """TB_CODE_DETAIL: 공통 코드 상세 (UI 드롭다운·라벨에 직접 사용)"""
    __tablename__ = "TB_CODE_DETAIL"

    group_cd: str = Column("GROUP_CD", String(50), primary_key=True, nullable=False)
    code_val: str = Column("CODE_VAL", String(50), primary_key=True, nullable=False)
    code_nm: str = Column("CODE_NM", String(100), nullable=False)
    code_desc: str | None = Column("CODE_DESC", String(500), nullable=True)
    sort_order: int = Column("SORT_ORDER", Integer, nullable=False)
    use_yn: str = Column("USE_YN", CHAR(1), nullable=False, server_default="Y")
    reg_dt: datetime = Column("REG_DT", DateTime, nullable=False, server_default=func.sysdate())
    reg_user_id: str = Column("REG_USER_ID", String(50), nullable=False)
    upd_dt: datetime | None = Column("UPD_DT", DateTime, nullable=True)
    upd_user_id: str | None = Column("UPD_USER_ID", String(50), nullable=True)

    group = relationship("CodeGroup", back_populates="details")


class ConsentItem(Base):
    """
    TB_CONSENT_ITEM: 개인정보 동의 항목 마스터 (10개)
    ← agent 도메인에서 common 도메인으로 이전 (경계 수정)
    Agent 신청 프로세스와 독립된 공통 마스터 데이터.
    """
    __tablename__ = "TB_CONSENT_ITEM"

    consent_item_id: str = Column(
        "CONSENT_ITEM_ID", String(36), primary_key=True, default=generate_uuid
    )
    item_nm: str = Column("ITEM_NM", String(200), nullable=False)
    item_desc: str | None = Column("ITEM_DESC", String(1000), nullable=True)
    sort_order: int = Column("SORT_ORDER", Integer, nullable=False)
    # CHECK 제약: 이진 플래그
    required_yn: str = Column("REQUIRED_YN", CHAR(1), nullable=False, server_default="Y")
    use_yn: str = Column("USE_YN", CHAR(1), nullable=False, server_default="Y")
    reg_dt: datetime = Column("REG_DT", DateTime, nullable=False, server_default=func.sysdate())

    # agent 도메인의 AgentConsent가 이 모델을 참조 (역방향 관계는 선언하지 않음)
    # → common → agent 방향의 의존성 생성을 방지
