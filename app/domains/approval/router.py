"""Admin 승인 라우터 (/api/admin)"""
import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_admin
from app.core.database import get_async_db
from app.core.schemas import MessageResponse, PaginatedResponse
from app.domains.agent.schemas import AgentResponse
from app.domains.agent.service import AgentService
from app.domains.approval.schemas import ApprovalRequestResponse, RejectRequest
from app.domains.approval.service import ApprovalService

router = APIRouter()


# ── Admin 전체 Agent 목록 ──────────────────────────
@router.get(
    "/agents",
    response_model=PaginatedResponse[AgentResponse],
    summary="전체 Agent 목록 조회 (Admin)",
)
async def list_all_agents(
    status_cd: str | None = Query(
        default=None,
        description="상태 필터 (PENDING/REJECTED/DEV/OPEN/DELETE_PENDING)",
    ),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    admin_user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """전체 Agent 목록을 조회합니다. (Admin 전용)"""
    agents, total = await AgentService(db).get_all_agents(status_cd, page, size)
    return PaginatedResponse(
        items=agents,
        total=total,
        page=page,
        size=size,
        total_pages=math.ceil(total / size) if total > 0 else 0,
    )


# ── 승인 요청 관리 ────────────────────────────────
@router.get(
    "/approvals",
    response_model=PaginatedResponse[ApprovalRequestResponse],
    summary="승인 요청 목록 조회 (Admin)",
)
async def list_approvals(
    status_cd: str | None = Query(
        default=None, description="처리 상태 필터 (PENDING/APPROVED/REJECTED)"
    ),
    req_type_cd: str | None = Query(
        default=None, description="요청 유형 필터 (CREATE/DELETE)"
    ),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    admin_user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """승인 요청 목록을 조회합니다. (Admin 전용, 반려 목록 포함)"""
    approvals, total = await ApprovalService(db).get_list(
        status_cd, req_type_cd, page, size
    )
    return PaginatedResponse(
        items=approvals,
        total=total,
        page=page,
        size=size,
        total_pages=math.ceil(total / size) if total > 0 else 0,
    )


@router.get(
    "/approvals/{approval_req_id}",
    response_model=ApprovalRequestResponse,
    summary="승인 요청 상세 조회 (Admin)",
)
async def get_approval(
    approval_req_id: str,
    admin_user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """승인 요청 상세 정보를 조회합니다. (Admin 전용)"""
    return await ApprovalService(db).get_detail(approval_req_id)


@router.post(
    "/approvals/{approval_req_id}/approve",
    response_model=ApprovalRequestResponse,
    summary="승인 처리 (Admin)",
)
async def approve_request(
    approval_req_id: str,
    admin_user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """
    승인 요청을 승인합니다. (Admin 전용)
    - CREATE 승인: PENDING → DEV
    - DELETE 승인: 소프트 삭제
    """
    return await ApprovalService(db).approve(approval_req_id, admin_user_id)


@router.post(
    "/approvals/{approval_req_id}/reject",
    response_model=ApprovalRequestResponse,
    summary="반려 처리 (Admin)",
)
async def reject_request(
    approval_req_id: str,
    body: RejectRequest,
    admin_user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """
    승인 요청을 반려합니다. (Admin 전용)
    - CREATE 반려: PENDING → REJECTED
    - DELETE 반려: DELETE_PENDING → 이전 상태 복원
    - 반려 사유 필수
    """
    return await ApprovalService(db).reject(approval_req_id, body, admin_user_id)
