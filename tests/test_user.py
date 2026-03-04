"""사용자 도메인 API 테스트
권한 체계: AGENT_SYSTEM_ADMIN(관리자) / AGENT_SYSTEM_USER(일반 사용자) 로만 운영
"""
from httpx import AsyncClient
from tests.conftest import ADMIN_ID, USER_ID, TEST_RUN_ID


class TestUserSync:
    async def test_sync_user_create(self, client: AsyncClient):
        """POST /api/users/sync - 사용자 동기화 (신규 생성)"""
        new_id = f"t-new-{TEST_RUN_ID}"
        resp = await client.post(
            "/api/users/sync",
            json={
                "user_id": new_id,
                "user_nm": "신규사용자",
                "email": "new@test.com",
                "emp_no": f"EMP-NEW-{TEST_RUN_ID}",
                "ext_system_id": "EXT_01",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == new_id
        assert data["user_nm"] == "신규사용자"
        assert data["sync_status"] == "SUCCESS"
        assert data["emp_no"] == f"EMP-NEW-{TEST_RUN_ID}"

    async def test_sync_user_update(self, client: AsyncClient):
        """POST /api/users/sync - 사용자 동기화 (기존 업데이트)"""
        resp = await client.post(
            "/api/users/sync",
            json={
                "user_id": USER_ID,
                "user_nm": "Updated User",
                "email": "updated@test.com",
                "ext_system_id": "EXT_01",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["user_nm"] == "Updated User"

    async def test_get_user(self, client: AsyncClient):
        """GET /api/users/{user_id} - 사용자 조회"""
        resp = await client.get(f"/api/users/{USER_ID}")
        assert resp.status_code == 200
        assert resp.json()["user_id"] == USER_ID

    async def test_get_user_not_found(self, client: AsyncClient):
        """GET /api/users/{user_id} - 존재하지 않는 사용자 → 404"""
        resp = await client.get("/api/users/nonexistent-user-id")
        assert resp.status_code == 404


# ── 외부 시스템 권한 동기화 ────────────────────────────────────
class TestExtPermission:
    async def test_list_ext_permissions(self, client: AsyncClient):
        """GET /api/users/ext-permissions - 외부 권한 마스터 목록"""
        resp = await client.get("/api/users/ext-permissions")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # AGENT_SYSTEM_USER, AGENT_SYSTEM_ADMIN 이 존재해야 함
        codes = [d["permission_cd"] for d in data]
        assert "AGENT_SYSTEM_USER" in codes
        assert "AGENT_SYSTEM_ADMIN" in codes

    async def test_sync_user_ext_permission(self, client: AsyncClient):
        """POST /api/users/ext-permissions/sync - 사용자 외부 권한 동기화"""
        resp = await client.post(
            "/api/users/ext-permissions/sync",
            json={
                "user_id": USER_ID,
                "permission_cd": "AGENT_SYSTEM_USER",
                "grant_yn": "Y",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["user_id"] == USER_ID
        assert data["grant_yn"] == "Y"

    async def test_sync_user_ext_permission_upsert(self, client: AsyncClient):
        """POST /api/users/ext-permissions/sync - 동일 권한 재동기화 (upsert)"""
        payload = {
            "user_id": USER_ID,
            "permission_cd": "AGENT_SYSTEM_USER",
            "grant_yn": "Y",
        }
        await client.post("/api/users/ext-permissions/sync", json=payload)
        resp = await client.post("/api/users/ext-permissions/sync", json=payload)
        assert resp.status_code == 201  # 두 번 호출해도 201

    async def test_sync_ext_permission_invalid_code(self, client: AsyncClient):
        """POST /api/users/ext-permissions/sync - 존재하지 않는 권한 코드 → 404"""
        resp = await client.post(
            "/api/users/ext-permissions/sync",
            json={
                "user_id": USER_ID,
                "permission_cd": "INVALID_CODE",
                "grant_yn": "Y",
            },
        )
        assert resp.status_code == 404

    async def test_sync_ext_permission_invalid_user(self, client: AsyncClient):
        """POST /api/users/ext-permissions/sync - 존재하지 않는 사용자 → 404"""
        resp = await client.post(
            "/api/users/ext-permissions/sync",
            json={
                "user_id": "no-such-user",
                "permission_cd": "AGENT_SYSTEM_USER",
                "grant_yn": "Y",
            },
        )
        assert resp.status_code == 404


# ── USER_ID 권한 체크 ──────────────────────────────────────────
class TestPermissionCheck:
    async def test_check_permission_not_found(self, client: AsyncClient):
        """GET /api/users/permission-check?user_id=... - 존재하지 않는 USER_ID → found=False"""
        resp = await client.get(
            "/api/users/permission-check", params={"user_id": "unknown-user-id"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is False
        assert data["user_id"] == "unknown-user-id"
        assert data["agent_system_admin"] is False
        assert data["agent_system_user"] is False
        assert data["permission_level"] == "NONE"

    async def test_check_permission_agent_system_user(self, client: AsyncClient):
        """GET /api/users/permission-check?user_id=... - AGENT_SYSTEM_USER 권한 확인"""
        resp = await client.get(
            "/api/users/permission-check", params={"user_id": USER_ID}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is True
        assert data["user_id"] == USER_ID
        assert data["agent_system_user"] is True
        assert data["agent_system_admin"] is False
        assert data["permission_level"] == "AGENT_SYSTEM_USER"

    async def test_check_permission_agent_system_admin(self, client: AsyncClient):
        """GET /api/users/permission-check?user_id=... - AGENT_SYSTEM_ADMIN 권한 확인"""
        resp = await client.get(
            "/api/users/permission-check", params={"user_id": ADMIN_ID}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is True
        assert data["user_id"] == ADMIN_ID
        assert data["agent_system_admin"] is True
        assert data["permission_level"] == "AGENT_SYSTEM_ADMIN"

    async def test_check_permission_level_priority(self, client: AsyncClient):
        """GET /api/users/permission-check - AGENT_SYSTEM_ADMIN이 최우선"""
        resp = await client.get(
            "/api/users/permission-check", params={"user_id": ADMIN_ID}
        )
        assert resp.status_code == 200
        assert resp.json()["permission_level"] == "AGENT_SYSTEM_ADMIN"
