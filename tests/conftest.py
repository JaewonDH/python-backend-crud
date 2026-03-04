"""
테스트 공통 픽스처
- Oracle DB에 직접 테스트 사용자/권한 삽입 (인증 치킨-에그 문제 우회)
- NullPool 비동기 엔진으로 get_async_db 의존성 오버라이드
  (테스트별 이벤트 루프 재생성 시 커넥션 풀 충돌 방지)
- 테스트 종료 후 생성한 데이터 전체 정리
"""
import uuid

import oracledb
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import get_async_db
from app.main import app

# 테스트 실행마다 고유 접두사 (병렬 실행 충돌 방지)
TEST_RUN_ID = str(uuid.uuid4())[:8]
ADMIN_ID = f"t-admin-{TEST_RUN_ID}"
USER_ID = f"t-user-{TEST_RUN_ID}"
DEV_ID = f"t-dev-{TEST_RUN_ID}"


# 세션 내에서 생성된 Agent ID 추적 (teardown 정리용)
_created_agent_ids: list[str] = []
# 테스트 중 동적으로 생성된 임시 사용자 ID 추적 (teardown 정리용)
_created_user_ids: list[str] = []

# ── NullPool 테스트 엔진 (이벤트 루프 충돌 방지) ─────────────────
_test_async_engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    poolclass=NullPool,  # 커넥션 풀 비활성화 → 이벤트 루프 재생성 안전
)
_TestAsyncSession = async_sessionmaker(
    bind=_test_async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def _override_get_async_db():
    """NullPool 세션으로 get_async_db 오버라이드"""
    async with _TestAsyncSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# FastAPI 의존성 오버라이드 적용
app.dependency_overrides[get_async_db] = _override_get_async_db


def _conn() -> oracledb.Connection:
    return oracledb.connect(
        user="myuser", password="mypassword", dsn="localhost:1521/FREEPDB1"
    )


def _placeholders(n: int) -> str:
    return ", ".join(f":{i + 1}" for i in range(n))


@pytest.fixture(scope="session", autouse=True)
def setup_test_users():
    """테스트 사용자 3명 + 외부 권한 직접 삽입 (TB_USER_EXT_PERMISSION)
    - ADMIN: AGENT_SYSTEM_ADMIN 권한
    - USER, DEV: AGENT_SYSTEM_USER 권한
    """
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

    # 외부 권한 ID 조회
    cur.execute(
        "SELECT EXT_PERMISSION_ID FROM TB_EXT_PERMISSION WHERE PERMISSION_CD = 'AGENT_SYSTEM_ADMIN'"
    )
    admin_perm_id = cur.fetchone()[0]
    cur.execute(
        "SELECT EXT_PERMISSION_ID FROM TB_EXT_PERMISSION WHERE PERMISSION_CD = 'AGENT_SYSTEM_USER'"
    )
    user_perm_id = cur.fetchone()[0]

    # ADMIN → AGENT_SYSTEM_ADMIN 권한 부여
    cur.execute(
        "INSERT INTO TB_USER_EXT_PERMISSION "
        "(USER_EXT_PERMISSION_ID, USER_ID, EXT_PERMISSION_ID, GRANT_YN) "
        "VALUES (:1, :2, :3, :4)",
        [str(uuid.uuid4()), ADMIN_ID, admin_perm_id, "Y"],
    )
    # USER, DEV → AGENT_SYSTEM_USER 권한 부여
    for uid in [USER_ID, DEV_ID]:
        cur.execute(
            "INSERT INTO TB_USER_EXT_PERMISSION "
            "(USER_EXT_PERMISSION_ID, USER_ID, EXT_PERMISSION_ID, GRANT_YN) "
            "VALUES (:1, :2, :3, :4)",
            [str(uuid.uuid4()), uid, user_perm_id, "Y"],
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
        # TB_AGENT_CONSENT_VALUE는 TB_AGENT_CONSENT의 자식 → 먼저 삭제
        cur.execute(
            f"DELETE FROM TB_AGENT_CONSENT_VALUE WHERE AGENT_CONSENT_ID IN "
            f"(SELECT AGENT_CONSENT_ID FROM TB_AGENT_CONSENT WHERE AGENT_ID IN ({ph}))",
            agent_ids,
        )
        cur.execute(f"DELETE FROM TB_AGENT_CONSENT WHERE AGENT_ID IN ({ph})", agent_ids)
        cur.execute(f"DELETE FROM TB_AGENT_MEMBER WHERE AGENT_ID IN ({ph})", agent_ids)
        cur.execute(
            f"DELETE FROM TB_APPROVAL_REQUEST WHERE AGENT_ID IN ({ph})", agent_ids
        )
        cur.execute(f"DELETE FROM TB_AGENT WHERE AGENT_ID IN ({ph})", agent_ids)

    cur.execute(f"DELETE FROM TB_USER_EXT_PERMISSION WHERE USER_ID IN ({ph3})", user_ids)
    cur.execute(f"DELETE FROM TB_USER_SYNC WHERE USER_ID IN ({ph3})", user_ids)

    # 테스트 중 동적으로 생성된 임시 사용자 정리
    extra_ids = list(set(_created_user_ids))
    if extra_ids:
        ph_extra = _placeholders(len(extra_ids))
        cur.execute(f"DELETE FROM TB_USER_EXT_PERMISSION WHERE USER_ID IN ({ph_extra})", extra_ids)
        cur.execute(f"DELETE FROM TB_USER_SYNC WHERE USER_ID IN ({ph_extra})", extra_ids)
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
async def consent_items(client: AsyncClient) -> list[dict]:
    """동의 항목 전체 정보 (item_type_cd 포함) — TEXT 타입 분기 처리용"""
    resp = await client.get("/api/common/consent-items")
    assert resp.status_code == 200, resp.text
    return resp.json()


def build_consent_payload(items: list[dict]) -> list[dict]:
    """동의 항목 타입에 따라 신청 payload 구성 (YN → agree_yn / TEXT → text_values)"""
    payload = []
    for item in items:
        if item.get("item_type_cd", "YN") == "TEXT":
            payload.append({
                "consent_item_id": item["consent_item_id"],
                "text_values": ["테스트 활용 목적 입력값"],
            })
        else:
            payload.append({
                "consent_item_id": item["consent_item_id"],
                "agree_yn": "Y",
            })
    return payload


@pytest_asyncio.fixture
async def created_agent(client: AsyncClient, user_headers: dict, consent_items: list[dict]):
    """테스트용 Agent 생성 픽스처 (PENDING 상태)"""
    resp = await client.post(
        "/api/agents/",
        json={
            "agent_nm": f"Test Agent {TEST_RUN_ID}",
            "agent_desc": "테스트용 Agent",
            "task_no": f"PRJ-{TEST_RUN_ID}",
            "team_nm": "AI개발팀",
            "charge_nm": "홍길동",
            "emp_no": "EMP001",
            "emp_nm": "홍길동",
            "group1_cd": "GRP1_A",
            "group2_cd": "GRP2_X",
            "consents": build_consent_payload(consent_items),
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
    consent_items: list[dict],
):
    """승인 완료된 Agent 픽스처 (DEV 상태)"""
    # Agent 생성
    resp = await client.post(
        "/api/agents/",
        json={
            "agent_nm": f"Approved Agent {TEST_RUN_ID}",
            "agent_desc": "승인된 Agent",
            "task_no": f"PRJ-APPR-{TEST_RUN_ID}",
            "team_nm": "운영팀",
            "charge_nm": "김철수",
            "emp_no": "EMP002",
            "emp_nm": "김철수",
            "group1_cd": "GRP1_A",
            "group2_cd": "GRP2_Y",
            "consents": build_consent_payload(consent_items),
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
