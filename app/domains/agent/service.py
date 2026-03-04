"""
Agent 도메인 서비스

[경계 수정]
1. ConsentItemService → common 도메인으로 이전됨
2. AgentStatusService 신규 추가:
   - approval 도메인이 Agent 리포지토리를 직접 접근하던 문제 해결
   - 승인/반려 시 Agent 상태 변경 + 이력 기록을 이 서비스가 캡슐화
   - approval/service.py 는 AgentStatusService 만 호출 (서비스↔서비스 의존)

의존 방향: approval → agent (단방향, 역방향 없음)
"""
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, ForbiddenException, NotFoundException
from app.domains.agent.models import Agent, AgentConsent, AgentConsentValue, AgentHistory, AgentMember
from app.domains.agent.repository import (
    AgentConsentRepository,
    AgentHistoryRepository,
    AgentMemberRepository,
    AgentRepository,
)
from app.domains.agent.schemas import AgentCreate, AgentMemberAdd, AgentUpdate


class AgentService:
    """Agent 카드 CRUD 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AgentRepository(db)
        self.member_repo = AgentMemberRepository(db)
        self.consent_repo = AgentConsentRepository(db)
        self.history_repo = AgentHistoryRepository(db)

    async def create_agent(self, data: AgentCreate, user_id: str) -> Agent:
        """
        Agent 카드 신청:
        1. TB_AGENT 생성 (PENDING) — 과제번호/팀이름/담당/사번/이름/그룹1/그룹2 포함
        2. TB_AGENT_MEMBER(AGENT_OWNER) 등록
        3. TB_AGENT_CONSENT 저장
        4. TB_APPROVAL_REQUEST(CREATE) 생성
        5. TB_AGENT_HISTORY(CREATE) 기록
        """
        # Agent 생성 (신규 필드 포함)
        agent = Agent(
            agent_nm=data.agent_nm,
            agent_desc=data.agent_desc,
            task_no=data.task_no,
            team_nm=data.team_nm,
            charge_nm=data.charge_nm,
            emp_no=data.emp_no,
            emp_nm=data.emp_nm,
            group1_cd=data.group1_cd,   # 그룹1 단일 선택
            group2_cd=data.group2_cd,   # 그룹2 단일 선택
            agent_status_cd="PENDING",
            owner_user_id=user_id,
            reg_user_id=user_id,
        )
        await self.repo.save(agent)

        # AGENT_OWNER 구성원 등록
        self.db.add(
            AgentMember(
                agent_id=agent.agent_id,
                user_id=user_id,
                role_cd="AGENT_OWNER",
                reg_user_id=user_id,
            )
        )

        # 동의 항목 저장 (YN 타입: agree_yn / TEXT 타입: text_values 여러 개)
        for c in data.consents:
            consent = AgentConsent(
                agent_id=agent.agent_id,
                consent_item_id=c.consent_item_id,
                agree_yn=c.agree_yn,        # TEXT 타입은 None
                user_id=user_id,
            )
            self.db.add(consent)
            await self.db.flush()           # consent_id 확보 후 값 저장
            for idx, val in enumerate(c.text_values, start=1):
                self.db.add(
                    AgentConsentValue(
                        agent_consent_id=consent.agent_consent_id,
                        text_value=val,
                        sort_order=idx,
                    )
                )
        await self.db.flush()

        # 승인 요청 생성 (approval 모델 직접 참조 — 생성만, 상태 변경 없음)
        from app.domains.approval.models import ApprovalRequest
        approval = ApprovalRequest(
            agent_id=agent.agent_id,
            req_type_cd="CREATE",
            req_status_cd="PENDING",
            req_user_id=user_id,
        )
        self.db.add(approval)
        await self.db.flush()

        # 이력 기록
        await self.history_repo.save(
            AgentHistory(
                agent_id=agent.agent_id,
                change_type_cd="CREATE",
                after_status_cd="PENDING",
                after_agent_nm=agent.agent_nm,
                after_agent_desc=agent.agent_desc,
                approval_req_id=approval.approval_req_id,
                reg_user_id=user_id,
            )
        )
        return agent

    async def get_agent(self, agent_id: str, user_id: str) -> Agent:
        """Agent 상세 조회 (OWNER 또는 DEV만)"""
        agent = await self.repo.find_by_id(agent_id)
        if not agent:
            raise NotFoundException(f"Agent를 찾을 수 없습니다. agent_id={agent_id}")
        await self._check_access(agent_id, user_id)
        return agent

    async def get_my_agents(
        self,
        user_id: str,
        status_cd: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Agent], int]:
        """내 Agent 목록 조회"""
        return await self.repo.find_my_agents(user_id, status_cd, (page - 1) * size, size)

    async def get_all_agents(
        self,
        status_cd: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Agent], int]:
        """전체 Agent 목록 조회 (Admin 전용)"""
        return await self.repo.find_all_agents(status_cd, (page - 1) * size, size)

    async def update_agent(
        self, agent_id: str, data: AgentUpdate, user_id: str
    ) -> Agent:
        """
        Agent 정보 수정 (OWNER 또는 DEV만):
        - 기본 정보(이름/설명/과제번호/팀이름/담당/사번/이름) 수정
        - 그룹 수정: None이면 변경 없음, 리스트(빈 리스트 포함)이면 전체 교체
        """
        agent = await self.repo.find_by_id(agent_id)
        if not agent:
            raise NotFoundException(f"Agent를 찾을 수 없습니다. agent_id={agent_id}")
        await self._check_access(agent_id, user_id)

        before_nm, before_desc = agent.agent_nm, agent.agent_desc

        # 기본 필드 수정
        if data.agent_nm is not None:
            agent.agent_nm = data.agent_nm
        if data.agent_desc is not None:
            agent.agent_desc = data.agent_desc
        if data.task_no is not None:
            agent.task_no = data.task_no
        if data.team_nm is not None:
            agent.team_nm = data.team_nm
        if data.charge_nm is not None:
            agent.charge_nm = data.charge_nm
        if data.emp_no is not None:
            agent.emp_no = data.emp_no
        if data.emp_nm is not None:
            agent.emp_nm = data.emp_nm
        # 그룹 수정 (None이 아닌 경우에만 갱신)
        if data.group1_cd is not None:
            agent.group1_cd = data.group1_cd
        if data.group2_cd is not None:
            agent.group2_cd = data.group2_cd
        agent.upd_user_id = user_id
        await self.db.flush()

        # 이력 기록
        await self.history_repo.save(
            AgentHistory(
                agent_id=agent_id,
                change_type_cd="UPDATE",
                before_agent_nm=before_nm,
                after_agent_nm=agent.agent_nm,
                before_agent_desc=before_desc,
                after_agent_desc=agent.agent_desc,
                reg_user_id=user_id,
            )
        )
        return agent

    async def request_delete_agent(self, agent_id: str, user_id: str) -> Agent:
        """
        Agent 삭제 요청 (OWNER만):
        1. 상태 → DELETE_PENDING
        2. TB_APPROVAL_REQUEST(DELETE) 생성
        3. TB_AGENT_HISTORY(DELETE_REQ) 기록
        """
        agent = await self.repo.find_by_id(agent_id)
        if not agent:
            raise NotFoundException(f"Agent를 찾을 수 없습니다. agent_id={agent_id}")
        await self._check_owner(agent_id, user_id)

        if agent.agent_status_cd == "DELETE_PENDING":
            raise BadRequestException("이미 삭제 요청 중인 Agent입니다.")
        if agent.agent_status_cd == "PENDING":
            raise BadRequestException("승인 대기 중인 Agent는 삭제 요청할 수 없습니다.")

        before_status = agent.agent_status_cd
        agent.agent_status_cd = "DELETE_PENDING"
        agent.upd_user_id = user_id
        await self.db.flush()

        from app.domains.approval.models import ApprovalRequest
        approval = ApprovalRequest(
            agent_id=agent_id,
            req_type_cd="DELETE",
            req_status_cd="PENDING",
            req_user_id=user_id,
        )
        self.db.add(approval)
        await self.db.flush()

        await self.history_repo.save(
            AgentHistory(
                agent_id=agent_id,
                change_type_cd="DELETE_REQ",
                before_status_cd=before_status,
                after_status_cd="DELETE_PENDING",
                approval_req_id=approval.approval_req_id,
                reg_user_id=user_id,
            )
        )
        return agent

    async def _check_access(self, agent_id: str, user_id: str) -> None:
        """OWNER 또는 DEV 여부 확인"""
        member = await self.member_repo.find_by_agent_and_user(agent_id, user_id)
        if not member:
            raise ForbiddenException("해당 Agent에 접근할 권한이 없습니다.")

    async def _check_owner(self, agent_id: str, user_id: str) -> None:
        """OWNER 여부 확인"""
        member = await self.member_repo.find_by_agent_and_user(agent_id, user_id)
        if not member or member.role_cd != "AGENT_OWNER":
            raise ForbiddenException("Agent Owner 권한이 필요합니다.")


class AgentMemberService:
    """Agent 구성원 관리 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent_repo = AgentRepository(db)
        self.member_repo = AgentMemberRepository(db)

    async def list_members(self, agent_id: str, user_id: str) -> list[AgentMember]:
        await self._check_access(agent_id, user_id)
        return await self.member_repo.find_by_agent(agent_id)

    async def add_member(
        self, agent_id: str, data: AgentMemberAdd, user_id: str
    ) -> AgentMember:
        """Agent 개발자 추가 (OWNER만)"""
        agent = await self.agent_repo.find_by_id(agent_id)
        if not agent:
            raise NotFoundException(f"Agent를 찾을 수 없습니다. agent_id={agent_id}")
        await self._check_owner(agent_id, user_id)

        if await self.member_repo.find_by_agent_and_user(agent_id, data.user_id):
            raise ConflictException(f"이미 등록된 구성원입니다. user_id={data.user_id}")

        member = AgentMember(
            agent_id=agent_id,
            user_id=data.user_id,
            role_cd=data.role_cd,
            reg_user_id=user_id,
        )
        return await self.member_repo.save(member)

    async def remove_member(
        self, agent_id: str, member_id: str, user_id: str
    ) -> None:
        """Agent 개발자 제거 (OWNER만, 소프트 삭제)"""
        await self._check_owner(agent_id, user_id)
        member = await self.member_repo.find_by_id(member_id)
        if not member or member.agent_id != agent_id:
            raise NotFoundException(f"구성원을 찾을 수 없습니다. member_id={member_id}")
        if member.role_cd == "AGENT_OWNER":
            raise BadRequestException("Agent Owner는 제거할 수 없습니다.")
        member.use_yn = "N"
        member.upd_user_id = user_id
        await self.db.flush()

    async def _check_access(self, agent_id: str, user_id: str) -> None:
        member = await self.member_repo.find_by_agent_and_user(agent_id, user_id)
        if not member:
            raise ForbiddenException("해당 Agent에 접근할 권한이 없습니다.")

    async def _check_owner(self, agent_id: str, user_id: str) -> None:
        member = await self.member_repo.find_by_agent_and_user(agent_id, user_id)
        if not member or member.role_cd != "AGENT_OWNER":
            raise ForbiddenException("Agent Owner 권한이 필요합니다.")


class AgentStatusService:
    """
    승인 처리에 의한 Agent 상태 변경 전용 서비스
    ─────────────────────────────────────────────
    [경계 수정] approval 도메인이 AgentRepository/AgentHistoryRepository를
    직접 접근하던 문제를 해결.
    approval/service.py 는 이 서비스만 호출 → 서비스↔서비스 의존 (리포지토리 직접 참조 제거)

    의존 방향: approval → agent.AgentStatusService (단방향)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent_repo = AgentRepository(db)
        self.history_repo = AgentHistoryRepository(db)

    async def on_create_approved(
        self, agent_id: str, approval_req_id: str, admin_user_id: str
    ) -> Agent:
        """신청 승인: PENDING → DEV"""
        agent = await self._get_agent(agent_id)
        before = agent.agent_status_cd
        agent.agent_status_cd = "DEV"
        agent.upd_user_id = admin_user_id
        await self.db.flush()
        await self.history_repo.save(
            AgentHistory(
                agent_id=agent_id,
                change_type_cd="STATUS_CHANGE",
                before_status_cd=before,
                after_status_cd="DEV",
                approval_req_id=approval_req_id,
                reg_user_id=admin_user_id,
            )
        )
        return agent

    async def on_create_rejected(
        self, agent_id: str, approval_req_id: str, admin_user_id: str
    ) -> Agent:
        """신청 반려: PENDING → REJECTED"""
        agent = await self._get_agent(agent_id)
        before = agent.agent_status_cd
        agent.agent_status_cd = "REJECTED"
        agent.upd_user_id = admin_user_id
        await self.db.flush()
        await self.history_repo.save(
            AgentHistory(
                agent_id=agent_id,
                change_type_cd="STATUS_CHANGE",
                before_status_cd=before,
                after_status_cd="REJECTED",
                approval_req_id=approval_req_id,
                reg_user_id=admin_user_id,
            )
        )
        return agent

    async def on_delete_approved(
        self, agent_id: str, approval_req_id: str, admin_user_id: str
    ) -> Agent:
        """삭제 승인: DELETE_PENDING → 소프트 삭제 (DEL_YN='Y')"""
        agent = await self._get_agent(agent_id)
        before = agent.agent_status_cd
        agent.del_yn = "Y"
        agent.del_dt = datetime.now()
        agent.del_user_id = admin_user_id
        agent.upd_user_id = admin_user_id
        await self.db.flush()
        await self.history_repo.save(
            AgentHistory(
                agent_id=agent_id,
                change_type_cd="DELETE",
                before_status_cd=before,
                after_status_cd="DELETED",
                approval_req_id=approval_req_id,
                reg_user_id=admin_user_id,
            )
        )
        return agent

    async def on_delete_rejected(
        self, agent_id: str, approval_req_id: str, admin_user_id: str
    ) -> Agent:
        """삭제 반려: DELETE_PENDING → 이전 상태(DEV/OPEN) 복원"""
        agent = await self._get_agent(agent_id)
        before = agent.agent_status_cd
        restored = await self._resolve_pre_delete_status(agent_id)
        agent.agent_status_cd = restored
        agent.upd_user_id = admin_user_id
        await self.db.flush()
        await self.history_repo.save(
            AgentHistory(
                agent_id=agent_id,
                change_type_cd="STATUS_CHANGE",
                before_status_cd=before,
                after_status_cd=restored,
                approval_req_id=approval_req_id,
                reg_user_id=admin_user_id,
            )
        )
        return agent

    async def _get_agent(self, agent_id: str) -> Agent:
        agent = await self.agent_repo.find_by_id_include_deleted(agent_id)
        if not agent:
            raise NotFoundException(f"Agent를 찾을 수 없습니다. agent_id={agent_id}")
        return agent

    async def _resolve_pre_delete_status(self, agent_id: str) -> str:
        """삭제 요청 이전 상태 이력 기반 조회 (기본값: DEV)"""
        last = await self.history_repo.find_last_status_before_delete(agent_id)
        return last.after_status_cd if last and last.after_status_cd else "DEV"
