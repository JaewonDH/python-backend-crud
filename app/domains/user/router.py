"""사용자 도메인 라우터 (/api/users)"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_admin
from app.core.database import get_async_db
from app.domains.user.schemas import (
    AgentSystemAccessCreate,
    AgentSystemAccessResponse,
    UserPermissionCreate,
    UserPermissionResponse,
    UserSyncCreate,
    UserSyncResponse,
)
from app.domains.user.service import (
    AgentSystemAccessService,
    UserPermissionService,
    UserSyncService,
)

router = APIRouter()


@router.post("/sync", response_model=UserSyncResponse, summary="사용자 동기화 (upsert)")
async def sync_user(
    body: UserSyncCreate,
    db: AsyncSession = Depends(get_async_db),
):
    """외부 시스템에서 사용자 정보를 동기화합니다."""
    return await UserSyncService(db).create_or_update_user(body)


@router.get("/{user_id}", response_model=UserSyncResponse, summary="사용자 조회")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    """사용자 정보를 조회합니다."""
    return await UserSyncService(db).get_user(user_id)


@router.post(
    "/access",
    response_model=AgentSystemAccessResponse,
    status_code=201,
    summary="시스템 접근 권한 부여 (Admin)",
)
async def grant_system_access(
    body: AgentSystemAccessCreate,
    admin_user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """Agent 시스템 접근 권한을 부여합니다. (Admin 전용)"""
    return await AgentSystemAccessService(db).grant_access(body, admin_user_id)


@router.post(
    "/permissions",
    response_model=UserPermissionResponse,
    status_code=201,
    summary="Admin 권한 부여 (Admin)",
)
async def grant_admin_permission(
    body: UserPermissionCreate,
    admin_user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """Admin 권한을 부여합니다. (Admin 전용)"""
    return await UserPermissionService(db).grant_admin(body, admin_user_id)
