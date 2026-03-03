"""승인 도메인 레포지토리"""
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.approval.models import ApprovalRequest


class ApprovalRequestRepository:
    """TB_APPROVAL_REQUEST CRUD"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_id(self, approval_req_id: str) -> ApprovalRequest | None:
        result = await self.db.execute(
            select(ApprovalRequest).where(
                ApprovalRequest.approval_req_id == approval_req_id
            )
        )
        return result.scalar_one_or_none()

    async def find_all(
        self,
        status_cd: str | None = None,
        req_type_cd: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[ApprovalRequest], int]:
        """승인 요청 목록 조회 (반려 포함, 상태·유형 필터)"""
        conditions = []
        if status_cd:
            conditions.append(ApprovalRequest.req_status_cd == status_cd)
        if req_type_cd:
            conditions.append(ApprovalRequest.req_type_cd == req_type_cd)

        base_cond = and_(*conditions) if conditions else True

        total = (
            await self.db.execute(
                select(func.count()).select_from(ApprovalRequest).where(base_cond)
            )
        ).scalar_one()

        result = await self.db.execute(
            select(ApprovalRequest)
            .where(base_cond)
            .order_by(ApprovalRequest.req_dt.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def save(self, approval: ApprovalRequest) -> ApprovalRequest:
        self.db.add(approval)
        await self.db.flush()
        return approval
