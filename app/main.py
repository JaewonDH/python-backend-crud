"""
FastAPI 애플리케이션 진입점
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.domains.agent.router import router as agent_router
from app.domains.approval.router import router as approval_router
from app.domains.common.router import router as common_router
from app.domains.user.router import router as user_router

app = FastAPI(
    title="Agent System API",
    description="Agent 카드 신청/승인 관리 시스템",
    version="0.1.0",
    debug=settings.app_debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 라우터 등록 ────────────────────────────────────
app.include_router(agent_router,    prefix="/api/agents",  tags=["Agent"])
app.include_router(approval_router, prefix="/api/admin",   tags=["Admin"])
app.include_router(common_router,   prefix="/api/common",  tags=["Common Code"])
app.include_router(user_router,     prefix="/api/users",   tags=["User"])


@app.get("/health", tags=["Health"])
async def health_check():
    """서버 상태 확인"""
    return {"status": "ok", "env": settings.app_env}
