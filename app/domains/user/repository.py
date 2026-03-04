"""사용자 도메인 레포지토리"""
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.user.models import ExtPermission, UserExtPermission, UserSync


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


class ExtPermissionRepository:
    """TB_EXT_PERMISSION CRUD"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_code(self, permission_cd: str) -> ExtPermission | None:
        result = await self.db.execute(
            select(ExtPermission).where(
                and_(ExtPermission.permission_cd == permission_cd, ExtPermission.use_yn == "Y")
            )
        )
        return result.scalar_one_or_none()

    async def find_all_active(self) -> list[ExtPermission]:
        result = await self.db.execute(
            select(ExtPermission).where(ExtPermission.use_yn == "Y")
        )
        return list(result.scalars().all())

    async def save(self, perm: ExtPermission) -> ExtPermission:
        self.db.add(perm)
        await self.db.flush()
        return perm


class UserExtPermissionRepository:
    """TB_USER_EXT_PERMISSION CRUD"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_active_by_user_and_code(
        self, user_id: str, permission_cd: str
    ) -> UserExtPermission | None:
        """특정 사용자의 특정 외부 권한 활성 여부 조회"""
        stmt = (
            select(UserExtPermission)
            .join(ExtPermission, UserExtPermission.ext_permission_id == ExtPermission.ext_permission_id)
            .where(
                and_(
                    UserExtPermission.user_id == user_id,
                    ExtPermission.permission_cd == permission_cd,
                    UserExtPermission.grant_yn == "Y",
                    (UserExtPermission.expire_dt.is_(None))
                    | (UserExtPermission.expire_dt > func.sysdate()),
                )
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_user_and_ext_permission(
        self, user_id: str, ext_permission_id: str
    ) -> UserExtPermission | None:
        result = await self.db.execute(
            select(UserExtPermission).where(
                and_(
                    UserExtPermission.user_id == user_id,
                    UserExtPermission.ext_permission_id == ext_permission_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def save(self, mapping: UserExtPermission) -> UserExtPermission:
        self.db.add(mapping)
        await self.db.flush()
        return mapping
