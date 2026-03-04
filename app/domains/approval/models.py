"""
승인 도메인 모델
- TB_APPROVAL_REQUEST: 승인 요청 관리 (생성/삭제)
"""
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import relationship

from app.models.base import Base, generate_uuid


class ApprovalRequest(Base):
    """TB_APPROVAL_REQUEST: 승인 요청 관리"""
    __tablename__ = "TB_APPROVAL_REQUEST"

    approval_req_id: str = Column(
        "APPROVAL_REQ_ID", String(36), primary_key=True, default=generate_uuid
    )
    agent_id: str = Column("AGENT_ID", String(36), ForeignKey("TB_AGENT.AGENT_ID"), nullable=False)
    # 코드 테이블 참조: REQ_TYPE_CD — CREATE / DELETE
    req_type_cd: str = Column("REQ_TYPE_CD", String(20), nullable=False)
    # 코드 테이블 참조: REQ_STATUS_CD — PENDING / APPROVED / REJECTED
    req_status_cd: str = Column(
        "REQ_STATUS_CD", String(20), nullable=False, server_default="PENDING"
    )
    req_user_id: str = Column("REQ_USER_ID", String(50), ForeignKey("TB_USER_SYNC.USER_ID"), nullable=False)
    req_dt: datetime = Column("REQ_DT", Date, nullable=False, server_default=func.sysdate())
    process_user_id: str | None = Column("PROCESS_USER_ID", String(50), ForeignKey("TB_USER_SYNC.USER_ID"), nullable=True)
    process_dt: datetime | None = Column("PROCESS_DT", Date, nullable=True)
    reject_reason: str | None = Column("REJECT_REASON", Text, nullable=True)
    reg_dt: datetime = Column("REG_DT", DateTime, nullable=False, server_default=func.sysdate())

    # 관계 정의
    agent = relationship("Agent", back_populates="approval_requests")
    req_user = relationship(
        "UserSync",
        primaryjoin="ApprovalRequest.req_user_id == UserSync.user_id",
        foreign_keys="ApprovalRequest.req_user_id",
    )
    process_user = relationship(
        "UserSync",
        primaryjoin="ApprovalRequest.process_user_id == UserSync.user_id",
        foreign_keys="ApprovalRequest.process_user_id",
    )
    histories = relationship(
        "AgentHistory",
        back_populates="approval_request",
        primaryjoin="ApprovalRequest.approval_req_id == AgentHistory.approval_req_id",
    )
