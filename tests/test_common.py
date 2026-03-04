"""공통 코드 도메인 API 테스트"""
import pytest
from httpx import AsyncClient
from tests.conftest import TEST_RUN_ID


class TestCodeGroup:
    async def test_list_code_groups(self, client: AsyncClient):
        """GET /api/common/code-groups - 코드 그룹 목록"""
        resp = await client.get("/api/common/code-groups")
        assert resp.status_code == 200
        groups = resp.json()
        assert isinstance(groups, list)
        assert len(groups) >= 4  # 마이그레이션으로 4개 생성
        group_cds = [g["group_cd"] for g in groups]
        assert "AGENT_STATUS_CD" in group_cds
        assert "ROLE_CD" in group_cds

    async def test_create_code_group(self, client: AsyncClient, admin_headers: dict):
        """POST /api/common/code-groups - 코드 그룹 등록 (Admin)"""
        group_cd = f"TEST_{TEST_RUN_ID}"
        resp = await client.post(
            "/api/common/code-groups",
            json={
                "group_cd": group_cd,
                "group_nm": "테스트 코드 그룹",
                "group_desc": "테스트용",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["group_cd"] == group_cd

    async def test_create_code_group_duplicate(
        self, client: AsyncClient, admin_headers: dict
    ):
        """POST /api/common/code-groups - 중복 그룹 코드 → 409"""
        resp = await client.post(
            "/api/common/code-groups",
            json={"group_cd": "AGENT_STATUS_CD", "group_nm": "중복"},
            headers=admin_headers,
        )
        assert resp.status_code == 409

    async def test_create_code_group_without_admin(self, client: AsyncClient):
        """POST /api/common/code-groups - Admin 없이 접근 → 401"""
        resp = await client.post(
            "/api/common/code-groups",
            json={"group_cd": "NO_AUTH", "group_nm": "권한없음"},
        )
        assert resp.status_code == 401


class TestCodeDetail:
    async def test_list_code_details(self, client: AsyncClient):
        """GET /api/common/code-groups/{group_cd}/details - 코드 상세 목록"""
        resp = await client.get("/api/common/code-groups/AGENT_STATUS_CD/details")
        assert resp.status_code == 200
        details = resp.json()
        assert isinstance(details, list)
        code_vals = [d["code_val"] for d in details]
        assert "PENDING" in code_vals
        assert "DEV" in code_vals

    async def test_list_code_details_not_found(self, client: AsyncClient):
        """GET /api/common/code-groups/{group_cd}/details - 없는 그룹 → 404"""
        resp = await client.get("/api/common/code-groups/NOT_EXIST/details")
        assert resp.status_code == 404

    async def test_create_code_detail(self, client: AsyncClient, admin_headers: dict):
        """POST /api/common/code-groups/{group_cd}/details - 코드 상세 등록"""
        group_cd = f"TEST_{TEST_RUN_ID}"
        # 그룹 먼저 생성
        await client.post(
            "/api/common/code-groups",
            json={"group_cd": group_cd, "group_nm": "테스트"},
            headers=admin_headers,
        )
        resp = await client.post(
            f"/api/common/code-groups/{group_cd}/details",
            json={"code_val": "VAL01", "code_nm": "값01", "sort_order": 1},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["code_val"] == "VAL01"


class TestConsentItem:
    async def test_list_consent_items(self, client: AsyncClient):
        """GET /api/common/consent-items - 동의 항목 목록"""
        resp = await client.get("/api/common/consent-items")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) >= 10  # 마이그레이션으로 최소 10개 생성
        # 필드 검증
        for item in items:
            assert "consent_item_id" in item
            assert "item_nm" in item
            assert "required_yn" in item

    async def test_create_consent_item(self, client: AsyncClient, admin_headers: dict):
        """POST /api/common/consent-items - 동의 항목 등록 (Admin)"""
        resp = await client.post(
            "/api/common/consent-items",
            json={
                "item_nm": f"추가동의항목 {TEST_RUN_ID}",
                "item_desc": "테스트 동의",
                "sort_order": 99,
                "required_yn": "N",
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["required_yn"] == "N"
