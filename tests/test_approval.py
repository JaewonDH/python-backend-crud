"""Admin 승인 도메인 API 테스트

커버 범위:
  GET  /api/admin/agents                           - 전체 Agent 목록 (Admin)
  GET  /api/admin/approvals                        - 승인 요청 목록
  GET  /api/admin/approvals?status_cd=...          - 상태 필터
  GET  /api/admin/approvals?req_type_cd=...        - 유형 필터
  GET  /api/admin/approvals/{id}                   - 상세 조회
  POST /api/admin/approvals/{id}/approve           - 승인 처리
  POST /api/admin/approvals/{id}/reject            - 반려 처리
"""
import pytest
from httpx import AsyncClient
from tests.conftest import USER_ID, TEST_RUN_ID


# ── 공통 헬퍼 ─────────────────────────────────────────────────
async def _get_pending_approval(client: AsyncClient, agent_id: str, admin_headers: dict) -> dict:
    """특정 Agent의 PENDING 상태 승인 요청 조회"""
    resp = await client.get(
        "/api/admin/approvals",
        params={"status_cd": "PENDING"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    approval = next(
        (a for a in resp.json()["items"] if a["agent_id"] == agent_id), None
    )
    assert approval is not None, f"PENDING 승인 요청 없음 (agent_id={agent_id})"
    return approval


# ── 전체 Agent 목록 (Admin) ───────────────────────────────────
class TestAdminAgentList:
    async def test_list_all_agents(
        self, client: AsyncClient, admin_headers: dict, created_agent: dict
    ):
        """GET /api/admin/agents - 전체 Agent 목록 조회"""
        resp = await client.get("/api/admin/agents", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "total_pages" in data
        assert data["total"] >= 1
        agent_ids = [a["agent_id"] for a in data["items"]]
        assert created_agent["agent_id"] in agent_ids

    async def test_list_all_agents_status_filter(
        self, client: AsyncClient, admin_headers: dict, created_agent: dict
    ):
        """GET /api/admin/agents?status_cd=PENDING - 상태 필터"""
        resp = await client.get(
            "/api/admin/agents",
            params={"status_cd": "PENDING"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        for agent in resp.json()["items"]:
            assert agent["agent_status_cd"] == "PENDING"

    async def test_list_all_agents_pagination(
        self, client: AsyncClient, admin_headers: dict, created_agent: dict
    ):
        """GET /api/admin/agents?page=1&size=1 - 페이지네이션"""
        resp = await client.get(
            "/api/admin/agents",
            params={"page": 1, "size": 1},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 1
        assert data["page"] == 1
        assert data["size"] == 1

    async def test_list_all_agents_requires_admin(
        self, client: AsyncClient, user_headers: dict
    ):
        """GET /api/admin/agents - 일반 사용자 → 403"""
        resp = await client.get("/api/admin/agents", headers=user_headers)
        assert resp.status_code == 403

    async def test_list_all_agents_requires_auth(self, client: AsyncClient):
        """GET /api/admin/agents - 인증 없음 → 401"""
        resp = await client.get("/api/admin/agents")
        assert resp.status_code == 401


# ── 승인 요청 목록 ────────────────────────────────────────────
class TestApprovalList:
    async def test_list_approvals(
        self, client: AsyncClient, admin_headers: dict, created_agent: dict
    ):
        """GET /api/admin/approvals - 승인 요청 목록"""
        resp = await client.get("/api/admin/approvals", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1
        # 생성된 Agent의 승인 요청이 존재해야 함
        agent_ids = [a["agent_id"] for a in data["items"]]
        assert created_agent["agent_id"] in agent_ids

    async def test_list_approvals_status_filter(
        self, client: AsyncClient, admin_headers: dict, created_agent: dict
    ):
        """GET /api/admin/approvals?status_cd=PENDING - 상태 필터"""
        resp = await client.get(
            "/api/admin/approvals",
            params={"status_cd": "PENDING"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        for approval in resp.json()["items"]:
            assert approval["req_status_cd"] == "PENDING"

    async def test_list_approvals_type_filter(
        self, client: AsyncClient, admin_headers: dict, created_agent: dict
    ):
        """GET /api/admin/approvals?req_type_cd=CREATE - 유형 필터"""
        resp = await client.get(
            "/api/admin/approvals",
            params={"req_type_cd": "CREATE"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        for approval in resp.json()["items"]:
            assert approval["req_type_cd"] == "CREATE"

    async def test_list_approvals_pagination(
        self, client: AsyncClient, admin_headers: dict, created_agent: dict
    ):
        """GET /api/admin/approvals?page=1&size=1 - 페이지네이션"""
        resp = await client.get(
            "/api/admin/approvals",
            params={"page": 1, "size": 1},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 1
        assert data["page"] == 1

    async def test_list_approvals_requires_admin(
        self, client: AsyncClient, user_headers: dict
    ):
        """GET /api/admin/approvals - 일반 사용자 → 403"""
        resp = await client.get("/api/admin/approvals", headers=user_headers)
        assert resp.status_code == 403


# ── 승인 요청 상세 조회 ───────────────────────────────────────
class TestApprovalDetail:
    async def test_get_approval_detail(
        self, client: AsyncClient, admin_headers: dict, created_agent: dict
    ):
        """GET /api/admin/approvals/{id} - 상세 조회"""
        approval = await _get_pending_approval(
            client, created_agent["agent_id"], admin_headers
        )
        resp = await client.get(
            f"/api/admin/approvals/{approval['approval_req_id']}",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["approval_req_id"] == approval["approval_req_id"]
        assert data["agent_id"] == created_agent["agent_id"]
        assert data["req_type_cd"] == "CREATE"
        assert data["req_status_cd"] == "PENDING"
        assert data["req_user_id"] == USER_ID

    async def test_get_approval_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        """GET /api/admin/approvals/{id} - 없는 ID → 404"""
        import uuid
        resp = await client.get(
            f"/api/admin/approvals/{uuid.uuid4()}",
            headers=admin_headers,
        )
        assert resp.status_code == 404

    async def test_get_approval_requires_admin(
        self, client: AsyncClient, user_headers: dict, created_agent: dict
    ):
        """GET /api/admin/approvals/{id} - 일반 사용자 → 403"""
        resp = await client.get(
            "/api/admin/approvals/some-id",
            headers=user_headers,
        )
        assert resp.status_code == 403


# ── 승인 처리 ─────────────────────────────────────────────────
class TestApprovalApprove:
    async def test_approve_create_request(
        self,
        client: AsyncClient,
        admin_headers: dict,
        user_headers: dict,
        consent_items: list[dict],
    ):
        """POST /api/admin/approvals/{id}/approve - CREATE 요청 승인 → DEV"""
        from tests.conftest import build_consent_payload, _created_agent_ids

        # 새 Agent 생성
        create_resp = await client.post(
            "/api/agents/",
            json={
                "agent_nm": f"Approve Test {TEST_RUN_ID}",
                "consents": build_consent_payload(consent_items),
            },
            headers=user_headers,
        )
        assert create_resp.status_code == 201
        agent_id = create_resp.json()["agent_id"]
        _created_agent_ids.append(agent_id)

        # 승인 요청 조회
        approval = await _get_pending_approval(client, agent_id, admin_headers)

        # 승인
        resp = await client.post(
            f"/api/admin/approvals/{approval['approval_req_id']}/approve",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["req_status_cd"] == "APPROVED"
        assert data["process_user_id"] is not None

        # Agent 상태 DEV 확인
        agent_resp = await client.get(f"/api/agents/{agent_id}", headers=user_headers)
        assert agent_resp.json()["agent_status_cd"] == "DEV"

    async def test_approve_already_processed(
        self,
        client: AsyncClient,
        admin_headers: dict,
        approved_agent: dict,
    ):
        """POST /api/admin/approvals/{id}/approve - 이미 승인된 요청 재승인 → 400"""
        # 이미 승인된 Agent의 승인 요청 조회 (APPROVED 상태)
        resp = await client.get(
            "/api/admin/approvals",
            params={"status_cd": "APPROVED", "req_type_cd": "CREATE"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        approval = next(
            (a for a in items if a["agent_id"] == approved_agent["agent_id"]), None
        )
        if approval is None:
            pytest.skip("승인 완료된 요청을 찾을 수 없음")

        resp = await client.post(
            f"/api/admin/approvals/{approval['approval_req_id']}/approve",
            headers=admin_headers,
        )
        assert resp.status_code == 400

    async def test_approve_requires_admin(
        self, client: AsyncClient, user_headers: dict
    ):
        """POST /api/admin/approvals/{id}/approve - 일반 사용자 → 403"""
        import uuid
        resp = await client.post(
            f"/api/admin/approvals/{uuid.uuid4()}/approve",
            headers=user_headers,
        )
        assert resp.status_code == 403


# ── 반려 처리 ─────────────────────────────────────────────────
class TestApprovalReject:
    async def test_reject_create_request(
        self,
        client: AsyncClient,
        admin_headers: dict,
        user_headers: dict,
        consent_items: list[dict],
    ):
        """POST /api/admin/approvals/{id}/reject - CREATE 요청 반려 → REJECTED"""
        from tests.conftest import build_consent_payload, _created_agent_ids

        # 새 Agent 생성
        create_resp = await client.post(
            "/api/agents/",
            json={
                "agent_nm": f"Reject Test {TEST_RUN_ID}",
                "consents": build_consent_payload(consent_items),
            },
            headers=user_headers,
        )
        assert create_resp.status_code == 201
        agent_id = create_resp.json()["agent_id"]
        _created_agent_ids.append(agent_id)

        # 승인 요청 조회
        approval = await _get_pending_approval(client, agent_id, admin_headers)

        # 반려
        resp = await client.post(
            f"/api/admin/approvals/{approval['approval_req_id']}/reject",
            json={"reject_reason": "테스트 반려 사유"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["req_status_cd"] == "REJECTED"
        assert data["reject_reason"] == "테스트 반려 사유"
        assert data["process_user_id"] is not None

        # Agent 상태 REJECTED 확인
        agent_resp = await client.get(f"/api/agents/{agent_id}", headers=user_headers)
        assert agent_resp.json()["agent_status_cd"] == "REJECTED"

    async def test_reject_without_reason(
        self,
        client: AsyncClient,
        admin_headers: dict,
        user_headers: dict,
        consent_items: list[dict],
    ):
        """POST /api/admin/approvals/{id}/reject - 반려 사유 없음 → 422"""
        from tests.conftest import build_consent_payload, _created_agent_ids

        create_resp = await client.post(
            "/api/agents/",
            json={
                "agent_nm": f"RejectNoReason {TEST_RUN_ID}",
                "consents": build_consent_payload(consent_items),
            },
            headers=user_headers,
        )
        assert create_resp.status_code == 201
        agent_id = create_resp.json()["agent_id"]
        _created_agent_ids.append(agent_id)

        approval = await _get_pending_approval(client, agent_id, admin_headers)

        # reject_reason 누락 → 422 Unprocessable Entity
        resp = await client.post(
            f"/api/admin/approvals/{approval['approval_req_id']}/reject",
            json={},
            headers=admin_headers,
        )
        assert resp.status_code == 422

    async def test_reject_delete_request(
        self,
        client: AsyncClient,
        admin_headers: dict,
        user_headers: dict,
        approved_agent: dict,
    ):
        """POST /api/admin/approvals/{id}/reject - DELETE 요청 반려 → 이전 상태 복원"""
        agent_id = approved_agent["agent_id"]

        # 삭제 요청
        del_resp = await client.delete(
            f"/api/agents/{agent_id}", headers=user_headers
        )
        assert del_resp.status_code == 200

        # DELETE 유형의 PENDING 승인 요청 조회
        approval = await _get_pending_approval(client, agent_id, admin_headers)
        assert approval["req_type_cd"] == "DELETE"

        # 반려
        resp = await client.post(
            f"/api/admin/approvals/{approval['approval_req_id']}/reject",
            json={"reject_reason": "삭제 요청 반려"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["req_status_cd"] == "REJECTED"

        # Agent 상태 DEV로 복원 확인
        agent_resp = await client.get(f"/api/agents/{agent_id}", headers=user_headers)
        assert agent_resp.json()["agent_status_cd"] == "DEV"

    async def test_reject_requires_admin(
        self, client: AsyncClient, user_headers: dict
    ):
        """POST /api/admin/approvals/{id}/reject - 일반 사용자 → 403"""
        import uuid
        resp = await client.post(
            f"/api/admin/approvals/{uuid.uuid4()}/reject",
            json={"reject_reason": "test"},
            headers=user_headers,
        )
        assert resp.status_code == 403
