"""공통 코드 도메인 레포지토리"""
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.common.models import CodeDetail, CodeGroup, ConsentItem


class CodeGroupRepository:
    """TB_CODE_GROUP CRUD"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_all_active(self) -> list[CodeGroup]:
        result = await self.db.execute(
            select(CodeGroup).where(CodeGroup.use_yn == "Y").order_by(CodeGroup.group_cd)
        )
        return list(result.scalars().all())

    async def find_by_cd(self, group_cd: str) -> CodeGroup | None:
        result = await self.db.execute(
            select(CodeGroup).where(CodeGroup.group_cd == group_cd)
        )
        return result.scalar_one_or_none()

    async def save(self, group: CodeGroup) -> CodeGroup:
        self.db.add(group)
        await self.db.flush()
        return group


class CodeDetailRepository:
    """TB_CODE_DETAIL CRUD"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_group(self, group_cd: str) -> list[CodeDetail]:
        result = await self.db.execute(
            select(CodeDetail)
            .where(and_(CodeDetail.group_cd == group_cd, CodeDetail.use_yn == "Y"))
            .order_by(CodeDetail.sort_order)
        )
        return list(result.scalars().all())

    async def save(self, detail: CodeDetail) -> CodeDetail:
        self.db.add(detail)
        await self.db.flush()
        return detail


class ConsentItemRepository:
    """TB_CONSENT_ITEM CRUD (agent 도메인에서 이전)"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_all_active(self) -> list[ConsentItem]:
        result = await self.db.execute(
            select(ConsentItem)
            .where(ConsentItem.use_yn == "Y")
            .order_by(ConsentItem.sort_order)
        )
        return list(result.scalars().all())

    async def find_by_id(self, item_id: str) -> ConsentItem | None:
        result = await self.db.execute(
            select(ConsentItem).where(ConsentItem.consent_item_id == item_id)
        )
        return result.scalar_one_or_none()

    async def save(self, item: ConsentItem) -> ConsentItem:
        self.db.add(item)
        await self.db.flush()
        return item
