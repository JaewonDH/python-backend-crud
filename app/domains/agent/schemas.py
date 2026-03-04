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
    """
    Agent 신청 시 동의 항목 입력

    ITEM_TYPE_CD 에 따라 둘 중 하나만 사용:
      YN   타입 → agree_yn 필수 ('Y' or 'N'), text_values 무시
      TEXT 타입 → text_values 필수 (1개 이상), agree_yn 무시
    """
    consent_item_id: str
    agree_yn: str | None = None         # YN 타입 전용
    text_values: list[str] = []         # TEXT 타입 전용 (여러 개 입력)


class AgentConsentValueResponse(BaseModel):
    """TEXT 타입 동의 항목 입력값 응답"""
    consent_value_id: str
    agent_consent_id: str
    text_value: str
    sort_order: int
    reg_dt: datetime

    model_config = {"from_attributes": True}


class AgentConsentResponse(BaseModel):
    """동의 내역 응답"""
    agent_consent_id: str
    agent_id: str
    consent_item_id: str
    agree_yn: str | None                # TEXT 타입은 None
    agree_dt: datetime
    text_values: list[AgentConsentValueResponse] = []  # TEXT 타입 입력값

    model_config = {"from_attributes": True}


# ── Agent ──────────────────────────────────────────
class AgentCreate(BaseModel):
    """Agent 카드 신청 요청"""
    agent_nm: str
    agent_desc: str | None = None
    # 신청 시 입력 필드
    task_no: str | None = None          # 과제번호
    team_nm: str | None = None          # 팀이름
    charge_nm: str | None = None        # 담당
    emp_no: str | None = None           # 사번
    emp_nm: str | None = None           # 이름
    # 그룹 단일 선택: TB_CODE_DETAIL에서 1개 선택
    group1_cd: str | None = None        # 그룹1 선택 코드
    group2_cd: str | None = None        # 그룹2 선택 코드
    consents: list[AgentConsentInput]


class AgentUpdate(BaseModel):
    """Agent 정보 수정 요청"""
    agent_nm: str | None = None
    agent_desc: str | None = None
    task_no: str | None = None
    team_nm: str | None = None
    charge_nm: str | None = None
    emp_no: str | None = None
    emp_nm: str | None = None
    # None이면 변경 없음
    group1_cd: str | None = None
    group2_cd: str | None = None


class AgentResponse(BaseModel):
    """Agent 카드 응답"""
    agent_id: str
    agent_nm: str
    agent_desc: str | None
    task_no: str | None
    team_nm: str | None
    charge_nm: str | None
    emp_no: str | None
    emp_nm: str | None
    group1_cd: str | None
    group2_cd: str | None
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
