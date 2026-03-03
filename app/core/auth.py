"""
인증/권한 의존성 함수
- X-User-ID 헤더 기반 인증
- TB_AGENT_SYSTEM_ACCESS 기반 시스템 접근 권한 확인
- TB_USER_PERMISSION 기반 Admin 권한 확인
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
    TB_AGENT_SYSTEM_ACCESS.GRANT_YN='Y' 인 유효 레코드 확인 (없으면 403)
    순환 import 방지를 위해 함수 내 지연 import 사용.
    """
    from app.domains.user.models import AgentSystemAccess

    stmt = select(AgentSystemAccess).where(
        and_(
            AgentSystemAccess.user_id == user_id,
            AgentSystemAccess.grant_yn == "Y",
            (AgentSystemAccess.expire_dt.is_(None))
            | (AgentSystemAccess.expire_dt > func.sysdate()),
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
    TB_USER_PERMISSION.PERMISSION_CD='ADMIN' AND USE_YN='Y' 확인 (없으면 403)
    순환 import 방지를 위해 함수 내 지연 import 사용.
    """
    from app.domains.user.models import UserPermission

    stmt = select(UserPermission).where(
        and_(
            UserPermission.user_id == user_id,
            UserPermission.permission_cd == "ADMIN",
            UserPermission.use_yn == "Y",
        )
    )
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise ForbiddenException("Admin 권한이 필요합니다.")
    return user_id
