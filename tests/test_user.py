"""사용자 도메인 API 테스트"""
import pytest
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
                "ext_system_id": "EXT_01",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == new_id
        assert data["user_nm"] == "신규사용자"
        assert data["sync_status"] == "SUCCESS"

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

    async def test_grant_system_access_without_admin(self, client: AsyncClient):
        """POST /api/users/access - Admin 헤더 없이 접근 → 401"""
        resp = await client.post(
            "/api/users/access",
            json={"user_id": USER_ID, "grant_yn": "Y"},
        )
        assert resp.status_code == 401

    async def test_grant_system_access_with_admin(
        self, client: AsyncClient, admin_headers: dict
    ):
        """POST /api/users/access - Admin 권한으로 접근 권한 부여"""
        new_id = f"t-access-{TEST_RUN_ID}"
        # 사용자 먼저 생성
        await client.post(
            "/api/users/sync",
            json={
                "user_id": new_id,
                "user_nm": "Access Test",
                "email": f"{new_id}@test.com",
                "ext_system_id": "EXT_01",
            },
        )
        resp = await client.post(
            "/api/users/access",
            json={"user_id": new_id, "grant_yn": "Y"},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["grant_yn"] == "Y"

    async def test_grant_admin_permission(
        self, client: AsyncClient, admin_headers: dict
    ):
        """POST /api/users/permissions - Admin 권한 부여"""
        new_id = f"t-perm-{TEST_RUN_ID}"
        await client.post(
            "/api/users/sync",
            json={
                "user_id": new_id,
                "user_nm": "Perm Test",
                "email": f"{new_id}@test.com",
                "ext_system_id": "EXT_01",
            },
        )
        resp = await client.post(
            "/api/users/permissions",
            json={"user_id": new_id, "permission_cd": "ADMIN"},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["permission_cd"] == "ADMIN"

    async def test_grant_admin_permission_duplicate(
        self, client: AsyncClient, admin_headers: dict
    ):
        """POST /api/users/permissions - 중복 Admin 부여 → 409"""
        resp = await client.post(
            "/api/users/permissions",
            json={"user_id": ADMIN_ID, "permission_cd": "ADMIN"},
            headers=admin_headers,
        )
        assert resp.status_code == 409
