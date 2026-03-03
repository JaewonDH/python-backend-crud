"""
Agent 도메인 레포지토리

[경계 수정]
ConsentItemRepository 는 common 도메인으로 이전됨.
이 파일은 Agent / AgentMember / AgentConsent / AgentHistory 만 관리.
"""
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.agent.models import Agent, AgentConsent, AgentHistory, AgentMember


class AgentRepository:
    """TB_AGENT CRUD"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_id(self, agent_id: str) -> Agent | None:
        """소프트 삭제되지 않은 Agent 조회 (동의 내역 포함)"""
        result = await self.db.execute(
            select(Agent)
            .where(and_(Agent.agent_id == agent_id, Agent.del_yn == "N"))
            .options(selectinload(Agent.consents))
        )
        return result.scalar_one_or_none()

    async def find_by_id_include_deleted(self, agent_id: str) -> Agent | None:
        """소프트 삭제 포함 조회 (승인/반려 처리 시 사용)"""
        result = await self.db.execute(
            select(Agent).where(Agent.agent_id == agent_id)
        )
        return result.scalar_one_or_none()

    async def find_my_agents(
        self,
        user_id: str,
        status_cd: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Agent], int]:
        """사용자가 Owner 또는 Dev로 참여 중인 Agent 목록 (페이지네이션)"""
        member_agent_ids = (
            select(AgentMember.agent_id)
            .where(and_(AgentMember.user_id == user_id, AgentMember.use_yn == "Y"))
            .scalar_subquery()
        )
        base_cond = and_(Agent.del_yn == "N", Agent.agent_id.in_(member_agent_ids))
        if status_cd:
            base_cond = and_(base_cond, Agent.agent_status_cd == status_cd)

        total = (
            await self.db.execute(
                select(func.count()).select_from(Agent).where(base_cond)
            )
        ).scalar_one()

        result = await self.db.execute(
            select(Agent)
            .where(base_cond)
            .order_by(Agent.reg_dt.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def find_all_agents(
        self,
        status_cd: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Agent], int]:
        """전체 Agent 목록 조회 — Admin 전용 (페이지네이션)"""
        base_cond = Agent.del_yn == "N"
        if status_cd:
            base_cond = and_(base_cond, Agent.agent_status_cd == status_cd)

        total = (
            await self.db.execute(
                select(func.count()).select_from(Agent).where(base_cond)
            )
        ).scalar_one()

        result = await self.db.execute(
            select(Agent)
            .where(base_cond)
            .order_by(Agent.reg_dt.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def save(self, agent: Agent) -> Agent:
        self.db.add(agent)
        await self.db.flush()
        return agent


class AgentMemberRepository:
    """TB_AGENT_MEMBER CRUD"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_agent_and_user(
        self, agent_id: str, user_id: str
    ) -> AgentMember | None:
        result = await self.db.execute(
            select(AgentMember).where(
                and_(
                    AgentMember.agent_id == agent_id,
                    AgentMember.user_id == user_id,
                    AgentMember.use_yn == "Y",
                )
            )
        )
        return result.scalar_one_or_none()

    async def find_by_id(self, member_id: str) -> AgentMember | None:
        result = await self.db.execute(
            select(AgentMember).where(AgentMember.agent_member_id == member_id)
        )
        return result.scalar_one_or_none()

    async def find_by_agent(self, agent_id: str) -> list[AgentMember]:
        result = await self.db.execute(
            select(AgentMember).where(
                and_(AgentMember.agent_id == agent_id, AgentMember.use_yn == "Y")
            )
        )
        return list(result.scalars().all())

    async def save(self, member: AgentMember) -> AgentMember:
        self.db.add(member)
        await self.db.flush()
        return member


class AgentConsentRepository:
    """TB_AGENT_CONSENT CRUD"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_all(self, consents: list[AgentConsent]) -> list[AgentConsent]:
        for c in consents:
            self.db.add(c)
        await self.db.flush()
        return consents


class AgentHistoryRepository:
    """TB_AGENT_HISTORY CRUD"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_last_status_before_delete(
        self, agent_id: str
    ) -> AgentHistory | None:
        """DELETE_REQ 직전 상태 이력 조회 — 삭제 반려 시 상태 복원에 사용"""
        result = await self.db.execute(
            select(AgentHistory)
            .where(
                and_(
                    AgentHistory.agent_id == agent_id,
                    AgentHistory.change_type_cd.in_(["CREATE", "STATUS_CHANGE"]),
                    AgentHistory.after_status_cd.in_(["DEV", "OPEN"]),
                )
            )
            .order_by(AgentHistory.reg_dt.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def save(self, history: AgentHistory) -> AgentHistory:
        self.db.add(history)
        await self.db.flush()
        return history
