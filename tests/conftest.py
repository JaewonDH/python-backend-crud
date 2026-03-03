"""
테스트 공통 픽스처
- Oracle DB에 직접 테스트 사용자/권한 삽입 (인증 치킨-에그 문제 우회)
- 테스트 종료 후 생성한 데이터 전체 정리
"""
import uuid

import oracledb
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app

# 테스트 실행마다 고유 접두사 (병렬 실행 충돌 방지)
TEST_RUN_ID = str(uuid.uuid4())[:8]
ADMIN_ID = f"t-admin-{TEST_RUN_ID}"
USER_ID = f"t-user-{TEST_RUN_ID}"
DEV_ID = f"t-dev-{TEST_RUN_ID}"

# 세션 내에서 생성된 Agent ID 추적 (teardown 정리용)
_created_agent_ids: list[str] = []


def _conn() -> oracledb.Connection:
    return oracledb.connect(
        user="myuser", password="mypassword", dsn="localhost:1521/FREEPDB1"
    )


def _placeholders(n: int) -> str:
    return ", ".join(f":{i + 1}" for i in range(n))


@pytest.fixture(scope="session", autouse=True)
def setup_test_users():
    """테스트 사용자 3명 + 시스템 접근 권한 + Admin 권한 직접 삽입"""
    conn = _conn()
    cur = conn.cursor()

    for uid, nm in [
        (ADMIN_ID, "Test Admin"),
        (USER_ID, "Test User"),
        (DEV_ID, "Test Dev"),
    ]:
        cur.execute(
            "INSERT INTO TB_USER_SYNC "
            "(USER_ID, USER_NM, EMAIL, EXT_SYSTEM_ID, SYNC_STATUS) "
            "VALUES (:1, :2, :3, :4, :5)",
            [uid, nm, f"{uid}@test.com", "TEST_SYS", "SUCCESS"],
        )
        cur.execute(
            "INSERT INTO TB_AGENT_SYSTEM_ACCESS "
            "(ACCESS_ID, USER_ID, GRANT_YN) VALUES (:1, :2, :3)",
            [str(uuid.uuid4()), uid, "Y"],
        )

    # Admin 권한 부여
    cur.execute(
        "INSERT INTO TB_USER_PERMISSION "
        "(USER_PERMISSION_ID, USER_ID, PERMISSION_CD, REG_USER_ID) "
        "VALUES (:1, :2, :3, :4)",
        [str(uuid.uuid4()), ADMIN_ID, "ADMIN", "SYSTEM"],
    )
    conn.commit()
    conn.close()

    yield

    # ── 정리: FK 역순 삭제 ─────────────────────────────
    conn = _conn()
    cur = conn.cursor()
    user_ids = [ADMIN_ID, USER_ID, DEV_ID]
    ph3 = _placeholders(3)

    # 테스트 중 생성된 Agent 하위 데이터 삭제
    cur.execute(
        f"SELECT AGENT_ID FROM TB_AGENT WHERE OWNER_USER_ID IN ({ph3})", user_ids
    )
    agent_ids = [r[0] for r in cur.fetchall()] + _created_agent_ids
    agent_ids = list(set(agent_ids))

    if agent_ids:
        ph = _placeholders(len(agent_ids))
        cur.execute(f"DELETE FROM TB_AGENT_HISTORY WHERE AGENT_ID IN ({ph})", agent_ids)
        cur.execute(f"DELETE FROM TB_AGENT_CONSENT WHERE AGENT_ID IN ({ph})", agent_ids)
        cur.execute(f"DELETE FROM TB_AGENT_MEMBER WHERE AGENT_ID IN ({ph})", agent_ids)
        cur.execute(
            f"DELETE FROM TB_APPROVAL_REQUEST WHERE AGENT_ID IN ({ph})", agent_ids
        )
        cur.execute(f"DELETE FROM TB_AGENT WHERE AGENT_ID IN ({ph})", agent_ids)

    cur.execute(f"DELETE FROM TB_USER_PERMISSION WHERE USER_ID IN ({ph3})", user_ids)
    cur.execute(
        f"DELETE FROM TB_AGENT_SYSTEM_ACCESS WHERE USER_ID IN ({ph3})", user_ids
    )
    cur.execute(f"DELETE FROM TB_USER_SYNC WHERE USER_ID IN ({ph3})", user_ids)
    conn.commit()
    conn.close()


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def admin_headers() -> dict:
    return {"X-User-ID": ADMIN_ID}


@pytest.fixture
def user_headers() -> dict:
    return {"X-User-ID": USER_ID}


@pytest.fixture
def dev_headers() -> dict:
    return {"X-User-ID": DEV_ID}


@pytest_asyncio.fixture
async def consent_item_ids(client: AsyncClient) -> list[str]:
    """동의 항목 ID 목록 (마이그레이션으로 이미 10개 존재)"""
    resp = await client.get("/api/common/consent-items")
    assert resp.status_code == 200, resp.text
    return [item["consent_item_id"] for item in resp.json()]


@pytest_asyncio.fixture
async def created_agent(client: AsyncClient, user_headers: dict, consent_item_ids: list[str]):
    """테스트용 Agent 생성 픽스처 (PENDING 상태)"""
    resp = await client.post(
        "/api/agents/",
        json={
            "agent_nm": f"Test Agent {TEST_RUN_ID}",
            "agent_desc": "테스트용 Agent",
            "consents": [
                {"consent_item_id": cid, "agree_yn": "Y"} for cid in consent_item_ids
            ],
        },
        headers=user_headers,
    )
    assert resp.status_code == 201, resp.text
    agent = resp.json()
    _created_agent_ids.append(agent["agent_id"])
    return agent


@pytest_asyncio.fixture
async def approved_agent(
    client: AsyncClient,
    user_headers: dict,
    admin_headers: dict,
    consent_item_ids: list[str],
):
    """승인 완료된 Agent 픽스처 (DEV 상태)"""
    # Agent 생성
    resp = await client.post(
        "/api/agents/",
        json={
            "agent_nm": f"Approved Agent {TEST_RUN_ID}",
            "agent_desc": "승인된 Agent",
            "consents": [
                {"consent_item_id": cid, "agree_yn": "Y"} for cid in consent_item_ids
            ],
        },
        headers=user_headers,
    )
    assert resp.status_code == 201, resp.text
    agent = resp.json()
    _created_agent_ids.append(agent["agent_id"])

    # 승인 요청 목록에서 해당 Agent의 요청 ID 조회
    approvals_resp = await client.get(
        "/api/admin/approvals",
        params={"status_cd": "PENDING"},
        headers=admin_headers,
    )
    assert approvals_resp.status_code == 200
    approval = next(
        (a for a in approvals_resp.json()["items"] if a["agent_id"] == agent["agent_id"]),
        None,
    )
    assert approval is not None, "승인 요청을 찾을 수 없습니다"

    # 승인
    approve_resp = await client.post(
        f"/api/admin/approvals/{approval['approval_req_id']}/approve",
        headers=admin_headers,
    )
    assert approve_resp.status_code == 200, approve_resp.text
    return agent
