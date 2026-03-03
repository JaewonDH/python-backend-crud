"""공통 코드 도메인 서비스"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.domains.common.models import CodeDetail, CodeGroup, ConsentItem
from app.domains.common.repository import (
    CodeDetailRepository,
    CodeGroupRepository,
    ConsentItemRepository,
)
from app.domains.common.schemas import (
    CodeDetailCreate,
    CodeGroupCreate,
    ConsentItemCreate,
)


class CodeGroupService:
    """공통 코드 그룹 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CodeGroupRepository(db)

    async def get_all(self) -> list[CodeGroup]:
        return await self.repo.find_all_active()

    async def create(self, data: CodeGroupCreate, req_user_id: str) -> CodeGroup:
        existing = await self.repo.find_by_cd(data.group_cd)
        if existing:
            raise ConflictException(f"이미 존재하는 코드 그룹입니다. group_cd={data.group_cd}")
        group = CodeGroup(
            group_cd=data.group_cd,
            group_nm=data.group_nm,
            group_desc=data.group_desc,
            reg_user_id=req_user_id,
        )
        return await self.repo.save(group)


class CodeDetailService:
    """공통 코드 상세 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.group_repo = CodeGroupRepository(db)
        self.detail_repo = CodeDetailRepository(db)

    async def get_by_group(self, group_cd: str) -> list[CodeDetail]:
        group = await self.group_repo.find_by_cd(group_cd)
        if not group:
            raise NotFoundException(f"코드 그룹을 찾을 수 없습니다. group_cd={group_cd}")
        return await self.detail_repo.find_by_group(group_cd)

    async def create(
        self, group_cd: str, data: CodeDetailCreate, req_user_id: str
    ) -> CodeDetail:
        group = await self.group_repo.find_by_cd(group_cd)
        if not group:
            raise NotFoundException(f"코드 그룹을 찾을 수 없습니다. group_cd={group_cd}")
        detail = CodeDetail(
            group_cd=group_cd,
            code_val=data.code_val,
            code_nm=data.code_nm,
            code_desc=data.code_desc,
            sort_order=data.sort_order,
            reg_user_id=req_user_id,
        )
        return await self.detail_repo.save(detail)


class ConsentItemService:
    """동의 항목 서비스 (agent 도메인에서 이전, common 도메인이 소유)"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ConsentItemRepository(db)

    async def get_all_active(self) -> list[ConsentItem]:
        return await self.repo.find_all_active()

    async def create(self, data: ConsentItemCreate) -> ConsentItem:
        item = ConsentItem(
            item_nm=data.item_nm,
            item_desc=data.item_desc,
            sort_order=data.sort_order,
            required_yn=data.required_yn,
        )
        return await self.repo.save(item)
