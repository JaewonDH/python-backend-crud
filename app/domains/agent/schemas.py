"""
Agent 도메인 스키마 (Pydantic)

[경계 수정]
ConsentItemCreate / ConsentItemResponse 는 common 도메인으로 이전됨.
Agent 신청 시 동의 항목 입력(AgentConsentInput)만 이 도메인이 소유.
"""
from datetime import datetime
from pydantic import BaseModel


# ── AgentConsent 입력 ──────────────────────────────
class AgentConsentInput(BaseModel):
    """Agent 신청 시 동의 항목 입력 (consent_item_id 참조만 보유)"""
    consent_item_id: str
    agree_yn: str  # Y or N


class AgentConsentResponse(BaseModel):
    """동의 내역 응답"""
    agent_consent_id: str
    agent_id: str
    consent_item_id: str
    agree_yn: str
    agree_dt: datetime

    model_config = {"from_attributes": True}


# ── Agent ──────────────────────────────────────────
class AgentCreate(BaseModel):
    """Agent 카드 신청 요청"""
    agent_nm: str
    agent_desc: str | None = None
    consents: list[AgentConsentInput]


class AgentUpdate(BaseModel):
    """Agent 정보 수정 요청"""
    agent_nm: str | None = None
    agent_desc: str | None = None


class AgentResponse(BaseModel):
    """Agent 카드 응답"""
    agent_id: str
    agent_nm: str
    agent_desc: str | None
    agent_status_cd: str
    owner_user_id: str
    del_yn: str
    reg_dt: datetime
    upd_dt: datetime | None

    model_config = {"from_attributes": True}


class AgentDetailResponse(AgentResponse):
    """Agent 상세 응답 (동의 내역 포함)"""
    consents: list[AgentConsentResponse] = []


# ── AgentMember ────────────────────────────────────
class AgentMemberAdd(BaseModel):
    """Agent 개발자 추가 요청"""
    user_id: str
    role_cd: str = "AGENT_DEV"


class AgentMemberResponse(BaseModel):
    """Agent 구성원 응답"""
    agent_member_id: str
    agent_id: str
    user_id: str
    role_cd: str
    use_yn: str
    reg_dt: datetime

    model_config = {"from_attributes": True}
