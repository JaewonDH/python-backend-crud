"""
공통 코드 라우터 (/api/common)
- 코드 그룹/상세 조회·등록
- 동의 항목 조회·등록

[경계 수정 결과]
ConsentItem 관련 엔드포인트가 이제 common 도메인의 스키마/서비스만 참조.
기존의 app.agent.schemas / app.agent.service import 제거됨.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_admin
from app.core.database import get_async_db
from app.domains.common.schemas import (
    CodeDetailCreate,
    CodeDetailResponse,
    CodeGroupCreate,
    CodeGroupResponse,
    ConsentItemCreate,
    ConsentItemResponse,
)
from app.domains.common.service import CodeDetailService, CodeGroupService, ConsentItemService

router = APIRouter()


# ── 코드 그룹 ──────────────────────────────────────
@router.get(
    "/code-groups",
    response_model=list[CodeGroupResponse],
    summary="코드 그룹 전체 목록 조회",
)
async def list_code_groups(db: AsyncSession = Depends(get_async_db)):
    """사용 중인 코드 그룹 목록을 반환합니다."""
    return await CodeGroupService(db).get_all()


@router.post(
    "/code-groups",
    response_model=CodeGroupResponse,
    status_code=201,
    summary="코드 그룹 등록 (Admin)",
)
async def create_code_group(
    body: CodeGroupCreate,
    admin_user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """새 코드 그룹을 등록합니다. (Admin 전용)"""
    return await CodeGroupService(db).create(body, admin_user_id)


# ── 코드 상세 ──────────────────────────────────────
@router.get(
    "/code-groups/{group_cd}/details",
    response_model=list[CodeDetailResponse],
    summary="그룹별 코드 상세 목록 조회",
)
async def list_code_details(
    group_cd: str,
    db: AsyncSession = Depends(get_async_db),
):
    """특정 그룹의 코드 상세 목록을 반환합니다."""
    return await CodeDetailService(db).get_by_group(group_cd)


@router.post(
    "/code-groups/{group_cd}/details",
    response_model=CodeDetailResponse,
    status_code=201,
    summary="코드 상세 등록 (Admin)",
)
async def create_code_detail(
    group_cd: str,
    body: CodeDetailCreate,
    admin_user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """코드 그룹에 상세 코드를 등록합니다. (Admin 전용)"""
    return await CodeDetailService(db).create(group_cd, body, admin_user_id)


# ── 동의 항목 ──────────────────────────────────────
@router.get(
    "/consent-items",
    response_model=list[ConsentItemResponse],
    summary="동의 항목 목록 조회",
)
async def list_consent_items(db: AsyncSession = Depends(get_async_db)):
    """개인정보 동의 항목 목록을 반환합니다."""
    return await ConsentItemService(db).get_all_active()


@router.post(
    "/consent-items",
    response_model=ConsentItemResponse,
    status_code=201,
    summary="동의 항목 등록 (Admin)",
)
async def create_consent_item(
    body: ConsentItemCreate,
    admin_user_id: str = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """개인정보 동의 항목을 등록합니다. (Admin 전용)"""
    return await ConsentItemService(db).create(body)
