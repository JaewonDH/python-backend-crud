"""
인증/권한 의존성 함수
- X-User-ID 헤더 기반 인증
- TB_USER_EXT_PERMISSION 기반 권한 확인
  · AGENT_SYSTEM_USER  → 시스템 접근 권한 (일반 사용자)
  · AGENT_SYSTEM_ADMIN → 관리자 권한
"""
from fastapi import Depends, Header
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.exceptions import ForbiddenException, UnauthorizedException


async def get_current_user_id(
    x_user_id: str | None = Header(default=None, alias="X-User-ID"),
) -> str:
    """X-User-ID 헤더에서 현재 사용자 ID 추출 (없으면 401)"""
    if not x_user_id:
        raise UnauthorizedException("X-User-ID 헤더가 필요합니다.")
    return x_user_id


async def require_system_access(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_db),
) -> str:
    """
    AGENT_SYSTEM_USER 또는 AGENT_SYSTEM_ADMIN 권한 보유 여부 확인 (없으면 403)
    순환 import 방지를 위해 함수 내 지연 import 사용.
    """
    from app.domains.user.models import ExtPermission, UserExtPermission

    stmt = (
        select(UserExtPermission)
        .join(ExtPermission, UserExtPermission.ext_permission_id == ExtPermission.ext_permission_id)
        .where(
            and_(
                UserExtPermission.user_id == user_id,
                ExtPermission.permission_cd.in_(["AGENT_SYSTEM_USER", "AGENT_SYSTEM_ADMIN"]),
                UserExtPermission.grant_yn == "Y",
                (UserExtPermission.expire_dt.is_(None))
                | (UserExtPermission.expire_dt > func.sysdate()),
            )
        )
    )
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise ForbiddenException("Agent 시스템 접근 권한이 없습니다.")
    return user_id


async def require_admin(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_db),
) -> str:
    """
    AGENT_SYSTEM_ADMIN 권한 보유 여부 확인 (없으면 403)
    순환 import 방지를 위해 함수 내 지연 import 사용.
    """
    from app.domains.user.models import ExtPermission, UserExtPermission

    stmt = (
        select(UserExtPermission)
        .join(ExtPermission, UserExtPermission.ext_permission_id == ExtPermission.ext_permission_id)
        .where(
            and_(
                UserExtPermission.user_id == user_id,
                ExtPermission.permission_cd == "AGENT_SYSTEM_ADMIN",
                UserExtPermission.grant_yn == "Y",
                (UserExtPermission.expire_dt.is_(None))
                | (UserExtPermission.expire_dt > func.sysdate()),
            )
        )
    )
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise ForbiddenException("Admin 권한이 필요합니다.")
    return user_id
