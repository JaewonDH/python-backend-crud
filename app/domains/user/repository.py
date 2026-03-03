"""사용자 도메인 레포지토리"""
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.user.models import AgentSystemAccess, UserPermission, UserSync


class UserSyncRepository:
    """TB_USER_SYNC CRUD"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_id(self, user_id: str) -> UserSync | None:
        result = await self.db.execute(
            select(UserSync).where(UserSync.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def save(self, user: UserSync) -> UserSync:
        self.db.add(user)
        await self.db.flush()
        return user


class AgentSystemAccessRepository:
    """TB_AGENT_SYSTEM_ACCESS CRUD"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_active_by_user_id(self, user_id: str) -> AgentSystemAccess | None:
        """유효한 접근 권한 조회 (만료되지 않은 건)"""
        stmt = select(AgentSystemAccess).where(
            and_(
                AgentSystemAccess.user_id == user_id,
                AgentSystemAccess.grant_yn == "Y",
                (AgentSystemAccess.expire_dt.is_(None))
                | (AgentSystemAccess.expire_dt > func.sysdate()),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self, access: AgentSystemAccess) -> AgentSystemAccess:
        self.db.add(access)
        await self.db.flush()
        return access


class UserPermissionRepository:
    """TB_USER_PERMISSION CRUD"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_admin_by_user_id(self, user_id: str) -> UserPermission | None:
        """Admin 권한 조회"""
        result = await self.db.execute(
            select(UserPermission).where(
                and_(
                    UserPermission.user_id == user_id,
                    UserPermission.permission_cd == "ADMIN",
                    UserPermission.use_yn == "Y",
                )
            )
        )
        return result.scalar_one_or_none()

    async def save(self, perm: UserPermission) -> UserPermission:
        self.db.add(perm)
        await self.db.flush()
        return perm
