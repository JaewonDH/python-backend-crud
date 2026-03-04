"""사용자 도메인 스키마 (Pydantic)
권한 체계: AGENT_SYSTEM_ADMIN(관리자) / AGENT_SYSTEM_USER(일반 사용자) 로만 운영
"""
from datetime import datetime
from pydantic import BaseModel


class UserSyncCreate(BaseModel):
    """사용자 동기화 생성/수정 요청"""
    user_id: str
    user_nm: str
    email: str
    dept_nm: str | None = None
    ext_system_id: str


class UserSyncResponse(BaseModel):
    """사용자 동기화 응답"""
    user_id: str
    user_nm: str
    email: str
    dept_nm: str | None
    ext_system_id: str
    sync_status: str
    sync_dt: datetime | None
    use_yn: str
    reg_dt: datetime

    model_config = {"from_attributes": True}


# ── 외부 시스템 권한 마스터 ─────────────────────────────────
class ExtPermissionResponse(BaseModel):
    """외부 시스템 권한 마스터 응답"""
    ext_permission_id: str
    permission_cd: str
    permission_nm: str
    description: str | None
    use_yn: str
    reg_dt: datetime

    model_config = {"from_attributes": True}


# ── 사용자-외부권한 매핑 ─────────────────────────────────────
class UserExtPermissionCreate(BaseModel):
    """사용자-외부권한 매핑 생성 요청 (외부 시스템 동기화용)"""
    user_id: str
    permission_cd: str  # AGENT_SYSTEM_USER / AGENT_SYSTEM_ADMIN
    grant_yn: str = "Y"
    expire_dt: datetime | None = None


class UserExtPermissionResponse(BaseModel):
    """사용자-외부권한 매핑 응답"""
    user_ext_permission_id: str
    user_id: str
    ext_permission_id: str
    grant_yn: str
    grant_dt: datetime
    expire_dt: datetime | None
    reg_dt: datetime

    model_config = {"from_attributes": True}


# ── USER_ID 권한 체크 응답 ──────────────────────────────────
class PermissionCheckResponse(BaseModel):
    """USER_ID 기반 권한 체크 응답
    - AGENT_SYSTEM_ADMIN: 관리자 (승인/반려, 전체 조회)
    - AGENT_SYSTEM_USER: 일반 사용자 (카드 신청, 조회)
    - permission_level: 대표 권한 (AGENT_SYSTEM_ADMIN > AGENT_SYSTEM_USER > NONE)
    """
    user_id: str
    user_nm: str | None
    found: bool  # USER_ID로 사용자 조회 여부

    # 권한 상세
    agent_system_admin: bool  # AGENT_SYSTEM_ADMIN 권한 보유
    agent_system_user: bool   # AGENT_SYSTEM_USER 권한 보유

    # 대표 권한 레벨 (우선순위: AGENT_SYSTEM_ADMIN > AGENT_SYSTEM_USER > NONE)
    permission_level: str
