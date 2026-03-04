"""외부 시스템 권한 동기화 테이블 추가

003 이 적용된 환경에서 다음을 수행:
  1. TB_USER_SYNC 에 EMP_NO 컬럼 추가 (사번)
  2. TB_EXT_PERMISSION 신규 생성 (외부 권한 마스터)
  3. TB_USER_EXT_PERMISSION 신규 생성 (사용자-외부권한 SET 매핑)
  4. 초기 권한 마스터 데이터 삽입
     - AGENT_SYSTEM_USER: Agent System User
     - AGENT_SYSTEM_ADMIN: Agent System Admin

Revision ID: 004
Revises: 003
Create Date: 2026-03-04
"""
import uuid
from typing import Sequence, Union

from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. TB_USER_SYNC 에 EMP_NO 컬럼 추가 ─────────────────
    op.execute("ALTER TABLE TB_USER_SYNC ADD EMP_NO VARCHAR2(50)")
    op.execute("COMMENT ON COLUMN TB_USER_SYNC.EMP_NO IS '사번 (외부 시스템 식별자)'")
    op.execute("CREATE INDEX IDX_USER_SYNC_EMP_NO ON TB_USER_SYNC (EMP_NO)")

    # ── 2. TB_EXT_PERMISSION 생성 ────────────────────────────
    op.execute("""
        CREATE TABLE TB_EXT_PERMISSION (
            EXT_PERMISSION_ID  VARCHAR2(36)   NOT NULL,
            PERMISSION_CD      VARCHAR2(50)   NOT NULL,
            PERMISSION_NM      VARCHAR2(100)  NOT NULL,
            DESCRIPTION        VARCHAR2(500),
            USE_YN             CHAR(1)        DEFAULT 'Y' NOT NULL
                                 CONSTRAINT CK_EXT_PERM_USE CHECK (USE_YN IN ('Y','N')),
            REG_DT             DATE           DEFAULT SYSDATE NOT NULL,
            CONSTRAINT PK_EXT_PERMISSION PRIMARY KEY (EXT_PERMISSION_ID),
            CONSTRAINT UQ_EXT_PERM_CD    UNIQUE (PERMISSION_CD)
        )
    """)
    op.execute("COMMENT ON TABLE  TB_EXT_PERMISSION IS '외부 시스템 권한 마스터 (Agent System User / Agent System Admin)'")
    op.execute("COMMENT ON COLUMN TB_EXT_PERMISSION.EXT_PERMISSION_ID IS '권한 ID (PK) - UUID'")
    op.execute("COMMENT ON COLUMN TB_EXT_PERMISSION.PERMISSION_CD     IS '권한 코드 (UNIQUE): AGENT_SYSTEM_USER / AGENT_SYSTEM_ADMIN'")
    op.execute("COMMENT ON COLUMN TB_EXT_PERMISSION.PERMISSION_NM     IS '권한명 (표시용)'")
    op.execute("COMMENT ON COLUMN TB_EXT_PERMISSION.USE_YN            IS '[CHECK] 사용여부 Y/N'")

    # ── 3. TB_USER_EXT_PERMISSION 생성 ───────────────────────
    op.execute("""
        CREATE TABLE TB_USER_EXT_PERMISSION (
            USER_EXT_PERMISSION_ID  VARCHAR2(36)  NOT NULL,
            USER_ID                 VARCHAR2(50)  NOT NULL,
            EXT_PERMISSION_ID       VARCHAR2(36)  NOT NULL,
            GRANT_YN                CHAR(1)       DEFAULT 'Y' NOT NULL
                                      CONSTRAINT CK_UEP_GRANT CHECK (GRANT_YN IN ('Y','N')),
            GRANT_DT                DATE          DEFAULT SYSDATE NOT NULL,
            EXPIRE_DT               DATE,
            SYNC_DT                 DATE,
            REG_DT                  DATE          DEFAULT SYSDATE NOT NULL,
            UPD_DT                  DATE,
            CONSTRAINT PK_USER_EXT_PERMISSION PRIMARY KEY (USER_EXT_PERMISSION_ID),
            CONSTRAINT FK_UEP_USER FOREIGN KEY (USER_ID)           REFERENCES TB_USER_SYNC(USER_ID),
            CONSTRAINT FK_UEP_PERM FOREIGN KEY (EXT_PERMISSION_ID) REFERENCES TB_EXT_PERMISSION(EXT_PERMISSION_ID),
            CONSTRAINT UQ_USER_EXT_PERM UNIQUE (USER_ID, EXT_PERMISSION_ID)
        )
    """)
    op.execute("COMMENT ON TABLE  TB_USER_EXT_PERMISSION IS '사용자-외부권한 SET 매핑 테이블 (외부 시스템 동기화)'")
    op.execute("COMMENT ON COLUMN TB_USER_EXT_PERMISSION.USER_EXT_PERMISSION_ID IS '매핑 ID (PK) - UUID'")
    op.execute("COMMENT ON COLUMN TB_USER_EXT_PERMISSION.GRANT_YN               IS '[CHECK] 권한 활성화 여부 Y/N'")
    op.execute("COMMENT ON COLUMN TB_USER_EXT_PERMISSION.EXPIRE_DT              IS '만료일시 (NULL=무기한)'")
    op.execute("CREATE INDEX IDX_UEP_USER ON TB_USER_EXT_PERMISSION (USER_ID, GRANT_YN)")
    op.execute("CREATE INDEX IDX_UEP_PERM ON TB_USER_EXT_PERMISSION (EXT_PERMISSION_ID)")

    # ── 4. 초기 권한 마스터 데이터 삽입 ─────────────────────
    user_perm_id = str(uuid.uuid4())
    admin_perm_id = str(uuid.uuid4())

    op.execute(
        f"INSERT INTO TB_EXT_PERMISSION (EXT_PERMISSION_ID, PERMISSION_CD, PERMISSION_NM, DESCRIPTION, USE_YN) "
        f"VALUES ('{user_perm_id}', 'AGENT_SYSTEM_USER', 'Agent System User', "
        f"'Agent 시스템 일반 사용 권한 (카드 신청, 조회 가능)', 'Y')"
    )
    op.execute(
        f"INSERT INTO TB_EXT_PERMISSION (EXT_PERMISSION_ID, PERMISSION_CD, PERMISSION_NM, DESCRIPTION, USE_YN) "
        f"VALUES ('{admin_perm_id}', 'AGENT_SYSTEM_ADMIN', 'Agent System Admin', "
        f"'Agent 시스템 관리자 권한 (승인/반려, 전체 조회 가능)', 'Y')"
    )


def downgrade() -> None:
    # 매핑 테이블 먼저 삭제 (FK 자식)
    op.execute("DROP TABLE TB_USER_EXT_PERMISSION CASCADE CONSTRAINTS PURGE")
    # 권한 마스터 삭제
    op.execute("DROP TABLE TB_EXT_PERMISSION CASCADE CONSTRAINTS PURGE")
    # 인덱스 삭제
    op.execute("DROP INDEX IDX_USER_SYNC_EMP_NO")
    # EMP_NO 컬럼 삭제
    op.execute("ALTER TABLE TB_USER_SYNC DROP COLUMN EMP_NO")
