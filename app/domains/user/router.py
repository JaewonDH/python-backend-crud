"""사용자 도메인 라우터 (/api/users)
권한 체계: AGENT_SYSTEM_ADMIN(관리자) / AGENT_SYSTEM_USER(일반 사용자) 로만 운영
주의: 정적 경로는 /{user_id} 동적 경로보다 먼저 등록
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.domains.user.schemas import (
    ExtPermissionResponse,
    PermissionCheckResponse,
    UserExtPermissionCreate,
    UserExtPermissionResponse,
    UserSyncCreate,
    UserSyncResponse,
)
from app.domains.user.service import (
    ExtPermissionService,
    UserExtPermissionService,
    UserSyncService,
)

router = APIRouter()


# ── 사용자 동기화 ─────────────────────────────────────────────
@router.post("/sync", response_model=UserSyncResponse, summary="사용자 동기화 (upsert)")
async def sync_user(
    body: UserSyncCreate,
    db: AsyncSession = Depends(get_async_db),
):
    """외부 시스템에서 사용자 정보를 동기화합니다."""
    return await UserSyncService(db).create_or_update_user(body)


# ── 외부 시스템 권한 마스터 (정적 경로 → /{user_id} 보다 앞에 위치) ──
@router.get(
    "/ext-permissions",
    response_model=list[ExtPermissionResponse],
    summary="외부 시스템 권한 마스터 목록",
)
async def list_ext_permissions(
    db: AsyncSession = Depends(get_async_db),
):
    """외부 시스템 권한 마스터 목록을 조회합니다. (AGENT_SYSTEM_USER / AGENT_SYSTEM_ADMIN)"""
    return await ExtPermissionService(db).get_all()


@router.post(
    "/ext-permissions/sync",
    response_model=UserExtPermissionResponse,
    status_code=201,
    summary="사용자-외부권한 동기화 (upsert)",
)
async def sync_user_ext_permission(
    body: UserExtPermissionCreate,
    db: AsyncSession = Depends(get_async_db),
):
    """외부 시스템이 사용자의 Agent System 권한(User/Admin)을 동기화합니다."""
    return await UserExtPermissionService(db).sync_permission(body)


# ── 사번 권한 체크 (정적 경로 → /{user_id} 보다 앞에 위치) ────
@router.get(
    "/permission-check",
    response_model=PermissionCheckResponse,
    summary="USER_ID로 권한 체크",
)
async def check_permission_by_user_id(
    user_id: str = Query(..., description="조회할 사용자 ID"),
    db: AsyncSession = Depends(get_async_db),
):
    """USER_ID로 Agent System 권한을 통합 체크합니다.

    - agent_system_admin: AGENT_SYSTEM_ADMIN 권한 보유 여부 (관리자)
    - agent_system_user: AGENT_SYSTEM_USER 권한 보유 여부 (일반 사용자)
    - permission_level: 대표 권한 (AGENT_SYSTEM_ADMIN > AGENT_SYSTEM_USER > NONE)
    """
    return await UserExtPermissionService(db).check_permissions_by_user_id(user_id)


# ── 동적 경로 (마지막에 위치해야 정적 경로와 충돌 없음) ──────
@router.get("/{user_id}", response_model=UserSyncResponse, summary="사용자 조회")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    """사용자 정보를 조회합니다."""
    return await UserSyncService(db).get_user(user_id)
