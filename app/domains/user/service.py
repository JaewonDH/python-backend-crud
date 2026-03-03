"""사용자 도메인 서비스"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.domains.user.models import AgentSystemAccess, UserPermission, UserSync
from app.domains.user.repository import (
    AgentSystemAccessRepository,
    UserPermissionRepository,
    UserSyncRepository,
)
from app.domains.user.schemas import (
    AgentSystemAccessCreate,
    UserPermissionCreate,
    UserSyncCreate,
)


class UserSyncService:
    """사용자 동기화 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserSyncRepository(db)

    async def get_user(self, user_id: str) -> UserSync:
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise NotFoundException(f"사용자를 찾을 수 없습니다. user_id={user_id}")
        return user

    async def create_or_update_user(self, data: UserSyncCreate) -> UserSync:
        """사용자 동기화 (upsert)"""
        user = await self.repo.find_by_id(data.user_id)
        if user:
            user.user_nm = data.user_nm
            user.email = data.email
            user.dept_nm = data.dept_nm
            user.ext_system_id = data.ext_system_id
            user.sync_status = "SUCCESS"
        else:
            user = UserSync(
                user_id=data.user_id,
                user_nm=data.user_nm,
                email=data.email,
                dept_nm=data.dept_nm,
                ext_system_id=data.ext_system_id,
                sync_status="SUCCESS",
            )
        return await self.repo.save(user)


class AgentSystemAccessService:
    """시스템 접근 권한 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AgentSystemAccessRepository(db)

    async def grant_access(
        self, data: AgentSystemAccessCreate, req_user_id: str
    ) -> AgentSystemAccess:
        """접근 권한 부여"""
        access = AgentSystemAccess(
            user_id=data.user_id,
            grant_yn=data.grant_yn,
            grant_reason=data.grant_reason,
            expire_dt=data.expire_dt,
        )
        return await self.repo.save(access)


class UserPermissionService:
    """Admin 권한 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserPermissionRepository(db)

    async def grant_admin(
        self, data: UserPermissionCreate, req_user_id: str
    ) -> UserPermission:
        """Admin 권한 부여 (중복 체크 포함)"""
        existing = await self.repo.find_admin_by_user_id(data.user_id)
        if existing:
            raise ConflictException(f"이미 Admin 권한이 존재합니다. user_id={data.user_id}")
        perm = UserPermission(
            user_id=data.user_id,
            permission_cd="ADMIN",
            reg_user_id=req_user_id,
        )
        return await self.repo.save(perm)
