"""사용자 도메인 서비스
권한 체계: AGENT_SYSTEM_ADMIN(관리자) / AGENT_SYSTEM_USER(일반 사용자) 로만 운영
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.domains.user.models import ExtPermission, UserExtPermission, UserSync
from app.domains.user.repository import (
    ExtPermissionRepository,
    UserExtPermissionRepository,
    UserSyncRepository,
)
from app.domains.user.schemas import (
    PermissionCheckResponse,
    UserExtPermissionCreate,
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


class ExtPermissionService:
    """외부 시스템 권한 마스터 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ExtPermissionRepository(db)

    async def get_all(self) -> list[ExtPermission]:
        return await self.repo.find_all_active()


class UserExtPermissionService:
    """사용자-외부권한 매핑 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ext_perm_repo = ExtPermissionRepository(db)
        self.mapping_repo = UserExtPermissionRepository(db)
        self.user_repo = UserSyncRepository(db)

    async def sync_permission(self, data: UserExtPermissionCreate) -> UserExtPermission:
        """외부 시스템 권한 동기화 (upsert)"""
        # 권한 마스터 조회
        ext_perm = await self.ext_perm_repo.find_by_code(data.permission_cd)
        if not ext_perm:
            raise NotFoundException(f"외부 권한 코드를 찾을 수 없습니다. permission_cd={data.permission_cd}")

        # 사용자 존재 체크
        user = await self.user_repo.find_by_id(data.user_id)
        if not user:
            raise NotFoundException(f"사용자를 찾을 수 없습니다. user_id={data.user_id}")

        # 기존 매핑 조회 (upsert)
        existing = await self.mapping_repo.find_by_user_and_ext_permission(
            data.user_id, ext_perm.ext_permission_id
        )
        if existing:
            existing.grant_yn = data.grant_yn
            existing.expire_dt = data.expire_dt
            return await self.mapping_repo.save(existing)

        mapping = UserExtPermission(
            user_id=data.user_id,
            ext_permission_id=ext_perm.ext_permission_id,
            grant_yn=data.grant_yn,
            expire_dt=data.expire_dt,
        )
        return await self.mapping_repo.save(mapping)

    async def check_permissions_by_user_id(self, user_id: str) -> PermissionCheckResponse:
        """USER_ID로 권한 통합 체크"""
        user = await self.user_repo.find_by_id(user_id)

        if not user:
            return PermissionCheckResponse(
                user_id=user_id,
                user_nm=None,
                found=False,
                agent_system_admin=False,
                agent_system_user=False,
                permission_level="NONE",
            )

        # 각 권한 조회
        agent_admin = await self.mapping_repo.find_active_by_user_and_code(
            user.user_id, "AGENT_SYSTEM_ADMIN"
        )
        agent_user = await self.mapping_repo.find_active_by_user_and_code(
            user.user_id, "AGENT_SYSTEM_USER"
        )

        is_agent_admin = agent_admin is not None
        is_agent_user = agent_user is not None

        # 우선순위에 따른 대표 권한 레벨 결정
        if is_agent_admin:
            level = "AGENT_SYSTEM_ADMIN"
        elif is_agent_user:
            level = "AGENT_SYSTEM_USER"
        else:
            level = "NONE"

        return PermissionCheckResponse(
            user_id=user.user_id,
            user_nm=user.user_nm,
            found=True,
            agent_system_admin=is_agent_admin,
            agent_system_user=is_agent_user,
            permission_level=level,
        )
