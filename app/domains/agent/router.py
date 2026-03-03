"""Agent 도메인 라우터 (/api/agents)"""
import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_system_access
from app.core.database import get_async_db
from app.core.schemas import MessageResponse, PaginatedResponse
from app.domains.agent.schemas import (
    AgentCreate,
    AgentDetailResponse,
    AgentMemberAdd,
    AgentMemberResponse,
    AgentResponse,
    AgentUpdate,
)
from app.domains.agent.service import AgentMemberService, AgentService

router = APIRouter()


# ── Agent CRUD ────────────────────────────────────
@router.post(
    "/",
    response_model=AgentResponse,
    status_code=201,
    summary="Agent 카드 신청",
)
async def create_agent(
    body: AgentCreate,
    user_id: str = Depends(require_system_access),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Agent 카드를 신청합니다.
    - 동의항목 포함 신청 / 신청 후 PENDING 상태
    - 신청자가 AGENT_OWNER 권한을 갖게 됨
    """
    return await AgentService(db).create_agent(body, user_id)


@router.get(
    "/",
    response_model=PaginatedResponse[AgentResponse],
    summary="내 Agent 목록 조회",
)
async def list_my_agents(
    status_cd: str | None = Query(
        default=None,
        description="상태 필터 (PENDING/REJECTED/DEV/OPEN/DELETE_PENDING)",
    ),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(require_system_access),
    db: AsyncSession = Depends(get_async_db),
):
    """Owner 또는 Dev로 참여 중인 Agent 목록을 조회합니다."""
    agents, total = await AgentService(db).get_my_agents(user_id, status_cd, page, size)
    return PaginatedResponse(
        items=agents,
        total=total,
        page=page,
        size=size,
        total_pages=math.ceil(total / size) if total > 0 else 0,
    )


@router.get(
    "/{agent_id}",
    response_model=AgentDetailResponse,
    summary="Agent 상세 조회",
)
async def get_agent(
    agent_id: str,
    user_id: str = Depends(require_system_access),
    db: AsyncSession = Depends(get_async_db),
):
    """Agent 상세 정보를 조회합니다. (OWNER 또는 DEV만)"""
    return await AgentService(db).get_agent(agent_id, user_id)


@router.put(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Agent 정보 수정",
)
async def update_agent(
    agent_id: str,
    body: AgentUpdate,
    user_id: str = Depends(require_system_access),
    db: AsyncSession = Depends(get_async_db),
):
    """Agent 이름, 설명 등을 수정합니다. (OWNER 또는 DEV만)"""
    return await AgentService(db).update_agent(agent_id, body, user_id)


@router.delete(
    "/{agent_id}",
    response_model=MessageResponse,
    summary="Agent 삭제 요청",
)
async def delete_agent(
    agent_id: str,
    user_id: str = Depends(require_system_access),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Agent 삭제를 요청합니다. (OWNER만)
    - DELETE_PENDING 상태로 변경 → Admin 승인 후 소프트 삭제
    """
    await AgentService(db).request_delete_agent(agent_id, user_id)
    return MessageResponse(message="삭제 요청이 접수되었습니다. Admin 승인 후 삭제됩니다.")


# ── Agent 구성원 관리 ─────────────────────────────
@router.get(
    "/{agent_id}/members",
    response_model=list[AgentMemberResponse],
    summary="Agent 구성원 목록 조회",
)
async def list_agent_members(
    agent_id: str,
    user_id: str = Depends(require_system_access),
    db: AsyncSession = Depends(get_async_db),
):
    """Agent 구성원 목록을 조회합니다."""
    return await AgentMemberService(db).list_members(agent_id, user_id)


@router.post(
    "/{agent_id}/members",
    response_model=AgentMemberResponse,
    status_code=201,
    summary="Agent 개발자 추가 (OWNER만)",
)
async def add_agent_member(
    agent_id: str,
    body: AgentMemberAdd,
    user_id: str = Depends(require_system_access),
    db: AsyncSession = Depends(get_async_db),
):
    """Agent 개발자를 추가합니다. (OWNER만)"""
    return await AgentMemberService(db).add_member(agent_id, body, user_id)


@router.delete(
    "/{agent_id}/members/{member_id}",
    response_model=MessageResponse,
    summary="Agent 개발자 제거 (OWNER만)",
)
async def remove_agent_member(
    agent_id: str,
    member_id: str,
    user_id: str = Depends(require_system_access),
    db: AsyncSession = Depends(get_async_db),
):
    """Agent 개발자를 제거합니다. (OWNER만)"""
    await AgentMemberService(db).remove_member(agent_id, member_id, user_id)
    return MessageResponse(message="구성원이 제거되었습니다.")
