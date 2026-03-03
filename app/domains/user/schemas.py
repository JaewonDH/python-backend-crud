"""사용자 도메인 스키마 (Pydantic)"""
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


class AgentSystemAccessCreate(BaseModel):
    """시스템 접근 권한 부여 요청"""
    user_id: str
    grant_yn: str = "Y"
    grant_reason: str | None = None
    expire_dt: datetime | None = None


class AgentSystemAccessResponse(BaseModel):
    """시스템 접근 권한 응답"""
    access_id: str
    user_id: str
    grant_yn: str
    grant_reason: str | None
    grant_dt: datetime
    expire_dt: datetime | None
    reg_dt: datetime

    model_config = {"from_attributes": True}


class UserPermissionCreate(BaseModel):
    """Admin 권한 부여 요청"""
    user_id: str
    permission_cd: str = "ADMIN"


class UserPermissionResponse(BaseModel):
    """Admin 권한 응답"""
    user_permission_id: str
    user_id: str
    permission_cd: str
    use_yn: str
    reg_dt: datetime

    model_config = {"from_attributes": True}
