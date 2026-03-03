"""
승인 도메인 서비스

[경계 수정]
기존: approval/service.py → AgentRepository, AgentHistoryRepository 직접 접근
개선: approval/service.py → AgentStatusService 호출 (서비스↔서비스 의존)

ApprovalService 는 승인 요청(TB_APPROVAL_REQUEST) 상태만 관리하고,
Agent 상태 변경 및 이력 기록은 AgentStatusService 에 위임함.

의존 방향: approval → agent (단방향, 역방향 없음)
"""
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.domains.agent.service import AgentStatusService  # 서비스↔서비스 의존
from app.domains.approval.models import ApprovalRequest
from app.domains.approval.repository import ApprovalRequestRepository
from app.domains.approval.schemas import RejectRequest


class ApprovalService:
    """승인/반려 처리 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ApprovalRequestRepository(db)
        self.agent_status_svc = AgentStatusService(db)  # 위임 서비스

    async def get_list(
        self,
        status_cd: str | None = None,
        req_type_cd: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[ApprovalRequest], int]:
        """승인 요청 목록 조회"""
        return await self.repo.find_all(status_cd, req_type_cd, (page - 1) * size, size)

    async def get_detail(self, approval_req_id: str) -> ApprovalRequest:
        """승인 요청 상세 조회"""
        req = await self.repo.find_by_id(approval_req_id)
        if not req:
            raise NotFoundException(
                f"승인 요청을 찾을 수 없습니다. approval_req_id={approval_req_id}"
            )
        return req

    async def approve(
        self, approval_req_id: str, admin_user_id: str
    ) -> ApprovalRequest:
        """
        승인 처리:
        - CREATE 요청: AgentStatusService.on_create_approved() 위임
        - DELETE 요청: AgentStatusService.on_delete_approved() 위임
        """
        req = await self._get_pending_request(approval_req_id)

        if req.req_type_cd == "CREATE":
            await self.agent_status_svc.on_create_approved(
                req.agent_id, approval_req_id, admin_user_id
            )
        elif req.req_type_cd == "DELETE":
            await self.agent_status_svc.on_delete_approved(
                req.agent_id, approval_req_id, admin_user_id
            )

        # 승인 요청 상태 업데이트 (approval 도메인 자체 책임)
        req.req_status_cd = "APPROVED"
        req.process_user_id = admin_user_id
        req.process_dt = datetime.now()
        await self.db.flush()
        return req

    async def reject(
        self, approval_req_id: str, data: RejectRequest, admin_user_id: str
    ) -> ApprovalRequest:
        """
        반려 처리:
        - CREATE 요청: AgentStatusService.on_create_rejected() 위임
        - DELETE 요청: AgentStatusService.on_delete_rejected() 위임 (이전 상태 복원)
        """
        req = await self._get_pending_request(approval_req_id)

        if req.req_type_cd == "CREATE":
            await self.agent_status_svc.on_create_rejected(
                req.agent_id, approval_req_id, admin_user_id
            )
        elif req.req_type_cd == "DELETE":
            await self.agent_status_svc.on_delete_rejected(
                req.agent_id, approval_req_id, admin_user_id
            )

        # 반려 요청 상태 업데이트 (approval 도메인 자체 책임)
        req.req_status_cd = "REJECTED"
        req.process_user_id = admin_user_id
        req.process_dt = datetime.now()
        req.reject_reason = data.reject_reason
        await self.db.flush()
        return req

    async def _get_pending_request(self, approval_req_id: str) -> ApprovalRequest:
        """PENDING 상태 요청만 반환 (이미 처리된 요청은 400)"""
        req = await self.repo.find_by_id(approval_req_id)
        if not req:
            raise NotFoundException(
                f"승인 요청을 찾을 수 없습니다. approval_req_id={approval_req_id}"
            )
        if req.req_status_cd != "PENDING":
            raise BadRequestException(
                f"이미 처리된 승인 요청입니다. 현재 상태: {req.req_status_cd}"
            )
        return req
