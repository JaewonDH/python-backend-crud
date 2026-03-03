"""승인 도메인 스키마 (Pydantic)"""
from datetime import datetime
from pydantic import BaseModel


class ApprovalRequestResponse(BaseModel):
    """승인 요청 응답"""
    approval_req_id: str
    agent_id: str
    req_type_cd: str
    req_status_cd: str
    req_user_id: str
    req_dt: datetime
    process_user_id: str | None
    process_dt: datetime | None
    reject_reason: str | None
    reg_dt: datetime

    model_config = {"from_attributes": True}


class RejectRequest(BaseModel):
    """반려 요청 (반려 사유 필수)"""
    reject_reason: str
