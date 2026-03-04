"""인증/권한 체계 테스트

TB_USER_PERMISSION 제거 후 개선된 권한 체계 검증:
  - AGENT_SYSTEM_ADMIN: 관리자 (Admin 엔드포인트 + 시스템 접근 모두 허용)
  - AGENT_SYSTEM_USER: 일반 사용자 (시스템 접근만 허용, Admin 엔드포인트 차단)
  - 권한 없음: 모든 보호 엔드포인트 차단 (403)
  - 인증 없음: 401

커버 범위:
  require_system_access 의존성:
    - AGENT_SYSTEM_USER → 통과
    - AGENT_SYSTEM_ADMIN → 통과 (상위 권한)
    - 권한 없음 → 403
    - GRANT_YN=N (취소) → 403
    - X-User-ID 없음 → 401

  require_admin 의존성:
    - AGENT_SYSTEM_ADMIN → 통과
    - AGENT_SYSTEM_USER → 403
    - 권한 없음 → 403
    - X-User-ID 없음 → 401

  삭제된 엔드포인트:
    - POST /api/users/access     (TB_AGENT_SYSTEM_ACCESS 기반) → 404/405
    - POST /api/users/permissions (TB_USER_PERMISSION 기반)    → 404/405
"""
import pytest
from httpx import AsyncClient
from tests.conftest import (
    ADMIN_ID,
    USER_ID,
    TEST_RUN_ID,
    build_consent_payload,
    _created_agent_ids,
    _created_user_ids,
)


# ── 헬퍼: 임시 사용자 생성 ──────────────────────────────────────
async def _create_temp_user(client: AsyncClient, suffix: str) -> str:
    """테스트용 임시 사용자 생성 후 ID 반환 (teardown 목록에 등록)"""
    uid = f"t-auth-{suffix}-{TEST_RUN_ID}"
    resp = await client.post(
        "/api/users/sync",
        json={
            "user_id": uid,
            "user_nm": f"Auth Test {suffix}",
            "email": f"{uid}@test.com",
            "ext_system_id": "EXT_TEST",
        },
    )
    assert resp.status_code == 200
    _created_user_ids.append(uid)
    return uid


async def _grant_ext_permission(
    client: AsyncClient, user_id: str, permission_cd: str, grant_yn: str = "Y"
) -> None:
    """사용자에게 외부 권한 부여/취소"""
    resp = await client.post(
        "/api/users/ext-permissions/sync",
        json={"user_id": user_id, "permission_cd": permission_cd, "grant_yn": grant_yn},
    )
    assert resp.status_code == 201


# ── require_system_access 검증 ────────────────────────────────
class TestRequireSystemAccess:
    """AGENT_SYSTEM_USER 또는 AGENT_SYSTEM_ADMIN이어야 통과하는 엔드포인트 검증"""

    async def test_agent_system_user_can_list_agents(
        self, client: AsyncClient, user_headers: dict, created_agent: dict
    ):
        """AGENT_SYSTEM_USER → GET /api/agents/ 접근 가능"""
        resp = await client.get("/api/agents/", headers=user_headers)
        assert resp.status_code == 200

    async def test_agent_system_admin_can_also_list_agents(
        self, client: AsyncClient, admin_headers: dict
    ):
        """AGENT_SYSTEM_ADMIN → 상위 권한으로 시스템 접근(require_system_access)도 통과"""
        resp = await client.get("/api/agents/", headers=admin_headers)
        assert resp.status_code == 200

    async def test_no_auth_header_returns_401(self, client: AsyncClient):
        """X-User-ID 헤더 없음 → 401"""
        resp = await client.get("/api/agents/")
        assert resp.status_code == 401

    async def test_user_with_no_ext_permission_returns_403(self, client: AsyncClient):
        """ext 권한이 없는 사용자 → 403 (TB_USER_SYNC에도 없는 ID)"""
        resp = await client.get(
            "/api/agents/",
            headers={"X-User-ID": f"no-perm-user-{TEST_RUN_ID}"},
        )
        assert resp.status_code == 403

    async def test_revoked_permission_returns_403(self, client: AsyncClient):
        """AGENT_SYSTEM_USER 권한을 부여했다가 GRANT_YN=N 취소 → 403"""
        uid = await _create_temp_user(client, "revoke")

        # 권한 부여 → 접근 가능
        await _grant_ext_permission(client, uid, "AGENT_SYSTEM_USER", "Y")
        resp = await client.get("/api/agents/", headers={"X-User-ID": uid})
        assert resp.status_code == 200

        # 권한 취소 → 403
        await _grant_ext_permission(client, uid, "AGENT_SYSTEM_USER", "N")
        resp = await client.get("/api/agents/", headers={"X-User-ID": uid})
        assert resp.status_code == 403

    async def test_granted_permission_allows_access(self, client: AsyncClient):
        """권한 없는 사용자에게 AGENT_SYSTEM_USER 부여 → 즉시 접근 허용"""
        uid = await _create_temp_user(client, "grant")

        # 권한 없음 → 403
        resp = await client.get("/api/agents/", headers={"X-User-ID": uid})
        assert resp.status_code == 403

        # AGENT_SYSTEM_USER 부여 → 200
        await _grant_ext_permission(client, uid, "AGENT_SYSTEM_USER", "Y")
        resp = await client.get("/api/agents/", headers={"X-User-ID": uid})
        assert resp.status_code == 200

    async def test_agent_system_user_can_create_agent(
        self, client: AsyncClient, consent_items: list[dict]
    ):
        """AGENT_SYSTEM_USER 권한 사용자 → Agent 신청 가능"""
        uid = await _create_temp_user(client, "creator")
        await _grant_ext_permission(client, uid, "AGENT_SYSTEM_USER", "Y")

        resp = await client.post(
            "/api/agents/",
            json={
                "agent_nm": f"Auth Create Test {TEST_RUN_ID}",
                "consents": build_consent_payload(consent_items),
            },
            headers={"X-User-ID": uid},
        )
        assert resp.status_code == 201
        _created_agent_ids.append(resp.json()["agent_id"])


# ── require_admin 검증 ────────────────────────────────────────
class TestRequireAdmin:
    """AGENT_SYSTEM_ADMIN만 통과하는 Admin 엔드포인트 검증"""

    async def test_agent_system_admin_can_access_admin_endpoint(
        self, client: AsyncClient, admin_headers: dict
    ):
        """AGENT_SYSTEM_ADMIN → GET /api/admin/agents 접근 가능"""
        resp = await client.get("/api/admin/agents", headers=admin_headers)
        assert resp.status_code == 200

    async def test_agent_system_admin_can_list_approvals(
        self, client: AsyncClient, admin_headers: dict
    ):
        """AGENT_SYSTEM_ADMIN → GET /api/admin/approvals 접근 가능"""
        resp = await client.get("/api/admin/approvals", headers=admin_headers)
        assert resp.status_code == 200

    async def test_agent_system_user_blocked_from_admin_agents(
        self, client: AsyncClient, user_headers: dict
    ):
        """AGENT_SYSTEM_USER → GET /api/admin/agents 접근 불가 → 403"""
        resp = await client.get("/api/admin/agents", headers=user_headers)
        assert resp.status_code == 403

    async def test_agent_system_user_blocked_from_admin_approvals(
        self, client: AsyncClient, user_headers: dict
    ):
        """AGENT_SYSTEM_USER → GET /api/admin/approvals 접근 불가 → 403"""
        resp = await client.get("/api/admin/approvals", headers=user_headers)
        assert resp.status_code == 403

    async def test_agent_system_user_blocked_from_approve_action(
        self, client: AsyncClient, user_headers: dict
    ):
        """AGENT_SYSTEM_USER → POST /api/admin/approvals/{id}/approve 접근 불가 → 403"""
        import uuid
        resp = await client.post(
            f"/api/admin/approvals/{uuid.uuid4()}/approve",
            headers=user_headers,
        )
        assert resp.status_code == 403

    async def test_agent_system_user_blocked_from_reject_action(
        self, client: AsyncClient, user_headers: dict
    ):
        """AGENT_SYSTEM_USER → POST /api/admin/approvals/{id}/reject 접근 불가 → 403"""
        import uuid
        resp = await client.post(
            f"/api/admin/approvals/{uuid.uuid4()}/reject",
            json={"reject_reason": "test"},
            headers=user_headers,
        )
        assert resp.status_code == 403

    async def test_no_auth_header_returns_401_on_admin(self, client: AsyncClient):
        """X-User-ID 없음 → 401"""
        resp = await client.get("/api/admin/agents")
        assert resp.status_code == 401

    async def test_no_ext_permission_blocked_from_admin(self, client: AsyncClient):
        """ext 권한 없는 사용자 → Admin 엔드포인트 403"""
        resp = await client.get(
            "/api/admin/agents",
            headers={"X-User-ID": f"no-perm-{TEST_RUN_ID}"},
        )
        assert resp.status_code == 403

    async def test_new_admin_user_can_access_admin_endpoint(self, client: AsyncClient):
        """AGENT_SYSTEM_ADMIN 권한 신규 부여 → Admin 엔드포인트 즉시 접근 가능"""
        uid = await _create_temp_user(client, "new-admin")

        # Admin 권한 없음 → 403
        resp = await client.get("/api/admin/agents", headers={"X-User-ID": uid})
        assert resp.status_code == 403

        # AGENT_SYSTEM_ADMIN 부여 → 200
        await _grant_ext_permission(client, uid, "AGENT_SYSTEM_ADMIN", "Y")
        resp = await client.get("/api/admin/agents", headers={"X-User-ID": uid})
        assert resp.status_code == 200


# ── 제거된 엔드포인트 확인 ─────────────────────────────────────
class TestRemovedEndpoints:
    """TB_USER_PERMISSION / TB_AGENT_SYSTEM_ACCESS 기반 API 제거 검증"""

    async def test_old_grant_system_access_endpoint_removed(
        self, client: AsyncClient, admin_headers: dict
    ):
        """POST /api/users/access - 레거시 시스템 접근 부여 엔드포인트 제거됨"""
        resp = await client.post(
            "/api/users/access",
            json={"user_id": USER_ID, "grant_yn": "Y"},
            headers=admin_headers,
        )
        # 엔드포인트가 없으므로 404 또는 405 반환
        assert resp.status_code in (404, 405)

    async def test_old_grant_admin_permission_endpoint_removed(
        self, client: AsyncClient, admin_headers: dict
    ):
        """POST /api/users/permissions - TB_USER_PERMISSION 기반 Admin 부여 엔드포인트 제거됨"""
        resp = await client.post(
            "/api/users/permissions",
            json={"user_id": USER_ID, "permission_cd": "ADMIN"},
            headers=admin_headers,
        )
        assert resp.status_code in (404, 405)

    async def test_ext_permission_sync_is_the_new_way(self, client: AsyncClient):
        """POST /api/users/ext-permissions/sync - 새로운 권한 부여 방식 (정상 동작 확인)"""
        uid = await _create_temp_user(client, "new-way")
        resp = await client.post(
            "/api/users/ext-permissions/sync",
            json={"user_id": uid, "permission_cd": "AGENT_SYSTEM_USER", "grant_yn": "Y"},
        )
        assert resp.status_code == 201
        assert resp.json()["grant_yn"] == "Y"


# ── 권한 격리 검증 ─────────────────────────────────────────────
class TestPermissionIsolation:
    """각 권한이 정확히 해당 범위만 허용하는지 검증"""

    async def test_user_cannot_view_other_users_agent(
        self, client: AsyncClient, created_agent: dict
    ):
        """다른 사용자의 Agent 상세 조회 불가 → 403 (구성원 아님)"""
        uid = await _create_temp_user(client, "isolation")
        await _grant_ext_permission(client, uid, "AGENT_SYSTEM_USER", "Y")

        resp = await client.get(
            f"/api/agents/{created_agent['agent_id']}",
            headers={"X-User-ID": uid},
        )
        assert resp.status_code == 403

    async def test_admin_can_view_all_agents_regardless_of_ownership(
        self, client: AsyncClient, admin_headers: dict, created_agent: dict
    ):
        """AGENT_SYSTEM_ADMIN → 전체 Agent 조회 가능 (소유 여부 무관)"""
        resp = await client.get("/api/admin/agents", headers=admin_headers)
        assert resp.status_code == 200
        agent_ids = [a["agent_id"] for a in resp.json()["items"]]
        assert created_agent["agent_id"] in agent_ids

    async def test_agent_system_admin_can_also_use_system_as_user(
        self, client: AsyncClient, consent_items: list[dict]
    ):
        """AGENT_SYSTEM_ADMIN → Agent 신청(require_system_access)도 가능"""
        uid = await _create_temp_user(client, "admin-as-user")
        await _grant_ext_permission(client, uid, "AGENT_SYSTEM_ADMIN", "Y")

        resp = await client.post(
            "/api/agents/",
            json={
                "agent_nm": f"Admin As User {TEST_RUN_ID}",
                "consents": build_consent_payload(consent_items),
            },
            headers={"X-User-ID": uid},
        )
        assert resp.status_code == 201
        _created_agent_ids.append(resp.json()["agent_id"])
