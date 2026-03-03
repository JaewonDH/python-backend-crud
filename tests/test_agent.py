"""Agent 도메인 API 테스트"""
import pytest
from httpx import AsyncClient
from tests.conftest import USER_ID, DEV_ID, TEST_RUN_ID


class TestAgentCreate:
    async def test_create_agent(
        self,
        client: AsyncClient,
        user_headers: dict,
        consent_item_ids: list[str],
    ):
        """POST /api/agents/ - Agent 카드 신청"""
        resp = await client.post(
            "/api/agents/",
            json={
                "agent_nm": f"Create Test {TEST_RUN_ID}",
                "agent_desc": "생성 테스트",
                "consents": [
                    {"consent_item_id": cid, "agree_yn": "Y"}
                    for cid in consent_item_ids
                ],
            },
            headers=user_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["agent_nm"] == f"Create Test {TEST_RUN_ID}"
        assert data["agent_status_cd"] == "PENDING"
        assert data["owner_user_id"] == USER_ID
        assert data["del_yn"] == "N"
        assert "agent_id" in data
        assert "reg_dt" in data

    async def test_create_agent_no_auth(
        self, client: AsyncClient, consent_item_ids: list[str]
    ):
        """POST /api/agents/ - 인증 헤더 없이 → 401"""
        resp = await client.post(
            "/api/agents/",
            json={
                "agent_nm": "No Auth",
                "consents": [{"consent_item_id": consent_item_ids[0], "agree_yn": "Y"}],
            },
        )
        assert resp.status_code == 401

    async def test_create_agent_no_system_access(
        self, client: AsyncClient, consent_item_ids: list[str]
    ):
        """POST /api/agents/ - 시스템 접근 권한 없는 사용자 → 403"""
        resp = await client.post(
            "/api/agents/",
            json={
                "agent_nm": "No Access",
                "consents": [{"consent_item_id": consent_item_ids[0], "agree_yn": "Y"}],
            },
            headers={"X-User-ID": "unknown-user-no-access"},
        )
        assert resp.status_code == 403


class TestAgentList:
    async def test_list_my_agents(
        self, client: AsyncClient, user_headers: dict, created_agent: dict
    ):
        """GET /api/agents/ - 내 Agent 목록 조회"""
        resp = await client.get("/api/agents/", headers=user_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1
        agent_ids = [a["agent_id"] for a in data["items"]]
        assert created_agent["agent_id"] in agent_ids

    async def test_list_my_agents_status_filter(
        self, client: AsyncClient, user_headers: dict, created_agent: dict
    ):
        """GET /api/agents/?status_cd=PENDING - 상태 필터"""
        resp = await client.get(
            "/api/agents/", params={"status_cd": "PENDING"}, headers=user_headers
        )
        assert resp.status_code == 200
        for agent in resp.json()["items"]:
            assert agent["agent_status_cd"] == "PENDING"

    async def test_list_my_agents_pagination(
        self, client: AsyncClient, user_headers: dict, created_agent: dict
    ):
        """GET /api/agents/?page=1&size=1 - 페이지네이션"""
        resp = await client.get(
            "/api/agents/", params={"page": 1, "size": 1}, headers=user_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 1
        assert data["page"] == 1
        assert data["size"] == 1


class TestAgentDetail:
    async def test_get_agent_detail(
        self, client: AsyncClient, user_headers: dict, created_agent: dict
    ):
        """GET /api/agents/{agent_id} - Agent 상세 조회"""
        agent_id = created_agent["agent_id"]
        resp = await client.get(f"/api/agents/{agent_id}", headers=user_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_id"] == agent_id
        assert "consents" in data
        assert len(data["consents"]) == 10  # 동의항목 10개

    async def test_get_agent_not_found(
        self, client: AsyncClient, user_headers: dict
    ):
        """GET /api/agents/{agent_id} - 없는 Agent → 404"""
        resp = await client.get(
            f"/api/agents/{str(__import__('uuid').uuid4())}", headers=user_headers
        )
        assert resp.status_code == 404

    async def test_get_agent_forbidden(
        self, client: AsyncClient, dev_headers: dict, created_agent: dict
    ):
        """GET /api/agents/{agent_id} - 구성원이 아닌 사용자 → 403"""
        resp = await client.get(
            f"/api/agents/{created_agent['agent_id']}", headers=dev_headers
        )
        assert resp.status_code == 403


class TestAgentUpdate:
    async def test_update_agent(
        self, client: AsyncClient, user_headers: dict, created_agent: dict
    ):
        """PUT /api/agents/{agent_id} - Agent 정보 수정"""
        agent_id = created_agent["agent_id"]
        resp = await client.put(
            f"/api/agents/{agent_id}",
            json={"agent_nm": "Updated Name", "agent_desc": "수정된 설명"},
            headers=user_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_nm"] == "Updated Name"
        assert data["agent_desc"] == "수정된 설명"

    async def test_update_agent_forbidden(
        self, client: AsyncClient, dev_headers: dict, created_agent: dict
    ):
        """PUT /api/agents/{agent_id} - 구성원이 아닌 사용자 → 403"""
        resp = await client.put(
            f"/api/agents/{created_agent['agent_id']}",
            json={"agent_nm": "Forbidden"},
            headers=dev_headers,
        )
        assert resp.status_code == 403


class TestAgentMember:
    async def test_list_members(
        self, client: AsyncClient, user_headers: dict, created_agent: dict
    ):
        """GET /api/agents/{agent_id}/members - 구성원 목록"""
        resp = await client.get(
            f"/api/agents/{created_agent['agent_id']}/members", headers=user_headers
        )
        assert resp.status_code == 200
        members = resp.json()
        assert len(members) >= 1
        # OWNER가 존재해야 함
        roles = [m["role_cd"] for m in members]
        assert "AGENT_OWNER" in roles

    async def test_add_member(
        self, client: AsyncClient, user_headers: dict, created_agent: dict
    ):
        """POST /api/agents/{agent_id}/members - 개발자 추가"""
        resp = await client.post(
            f"/api/agents/{created_agent['agent_id']}/members",
            json={"user_id": DEV_ID, "role_cd": "AGENT_DEV"},
            headers=user_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["user_id"] == DEV_ID
        assert data["role_cd"] == "AGENT_DEV"

    async def test_add_member_duplicate(
        self, client: AsyncClient, user_headers: dict, created_agent: dict
    ):
        """POST /api/agents/{agent_id}/members - 중복 추가 → 409"""
        # DEV 이미 추가된 상태 (test_add_member 선행 필요)
        await client.post(
            f"/api/agents/{created_agent['agent_id']}/members",
            json={"user_id": DEV_ID, "role_cd": "AGENT_DEV"},
            headers=user_headers,
        )
        resp = await client.post(
            f"/api/agents/{created_agent['agent_id']}/members",
            json={"user_id": DEV_ID, "role_cd": "AGENT_DEV"},
            headers=user_headers,
        )
        assert resp.status_code == 409

    async def test_remove_member(
        self, client: AsyncClient, user_headers: dict, created_agent: dict
    ):
        """DELETE /api/agents/{agent_id}/members/{member_id} - 개발자 제거"""
        agent_id = created_agent["agent_id"]
        # 개발자 추가
        add_resp = await client.post(
            f"/api/agents/{agent_id}/members",
            json={"user_id": DEV_ID, "role_cd": "AGENT_DEV"},
            headers=user_headers,
        )
        # 이미 있으면 목록에서 찾기
        members_resp = await client.get(
            f"/api/agents/{agent_id}/members", headers=user_headers
        )
        members = members_resp.json()
        dev_member = next((m for m in members if m["user_id"] == DEV_ID and m["role_cd"] == "AGENT_DEV"), None)
        if not dev_member:
            pytest.skip("DEV 멤버 없음 - 이전 테스트 선행 필요")

        resp = await client.delete(
            f"/api/agents/{agent_id}/members/{dev_member['agent_member_id']}",
            headers=user_headers,
        )
        assert resp.status_code == 200

    async def test_add_member_not_owner(
        self, client: AsyncClient, dev_headers: dict, created_agent: dict
    ):
        """POST /api/agents/{agent_id}/members - OWNER가 아닌 사용자 → 403"""
        # DEV가 먼저 멤버로 추가되지 않은 경우 403 (접근 불가)
        resp = await client.post(
            f"/api/agents/{created_agent['agent_id']}/members",
            json={"user_id": "someone", "role_cd": "AGENT_DEV"},
            headers=dev_headers,
        )
        assert resp.status_code == 403


class TestAgentDelete:
    async def test_delete_pending_agent_should_fail(
        self, client: AsyncClient, user_headers: dict, created_agent: dict
    ):
        """DELETE /api/agents/{agent_id} - PENDING 상태는 삭제 요청 불가 → 400"""
        resp = await client.delete(
            f"/api/agents/{created_agent['agent_id']}", headers=user_headers
        )
        assert resp.status_code == 400

    async def test_request_delete_approved_agent(
        self, client: AsyncClient, user_headers: dict, approved_agent: dict
    ):
        """DELETE /api/agents/{agent_id} - DEV 상태 Agent 삭제 요청 → DELETE_PENDING"""
        agent_id = approved_agent["agent_id"]
        resp = await client.delete(f"/api/agents/{agent_id}", headers=user_headers)
        assert resp.status_code == 200

        # 상태 확인
        detail_resp = await client.get(f"/api/agents/{agent_id}", headers=user_headers)
        assert detail_resp.json()["agent_status_cd"] == "DELETE_PENDING"
