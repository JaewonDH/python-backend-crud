"""초기 테이블 생성 - Agent System v2 (UUID PK 적용)

Revision ID: 001
Revises:
Create Date: 2026-03-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """초기 테이블 전체 생성 (UUID PK 기반)"""

    # ── TB_USER_SYNC ─────────────────────────────────────────
    op.execute("""
        CREATE TABLE TB_USER_SYNC (
            USER_ID        VARCHAR2(50)   NOT NULL,
            USER_NM        VARCHAR2(100)  NOT NULL,
            EMAIL          VARCHAR2(200)  NOT NULL,
            DEPT_NM        VARCHAR2(200),
            EXT_SYSTEM_ID  VARCHAR2(50)   NOT NULL,
            SYNC_STATUS    VARCHAR2(20)   DEFAULT 'PENDING' NOT NULL
                             CONSTRAINT CK_USER_SYNC_STATUS
                             CHECK (SYNC_STATUS IN ('PENDING','SUCCESS','FAIL')),
            SYNC_DT        DATE,
            USE_YN         CHAR(1)        DEFAULT 'Y' NOT NULL
                             CONSTRAINT CK_USER_SYNC_USE CHECK (USE_YN IN ('Y','N')),
            REG_DT         DATE           DEFAULT SYSDATE NOT NULL,
            UPD_DT         DATE,
            CONSTRAINT PK_USER_SYNC PRIMARY KEY (USER_ID)
        )
    """)
    op.execute("COMMENT ON TABLE  TB_USER_SYNC IS '사용자 동기화 (외부 시스템)'")
    op.execute("COMMENT ON COLUMN TB_USER_SYNC.USER_ID IS '사용자 ID (PK) - 외부 시스템 식별자'")
    op.execute("COMMENT ON COLUMN TB_USER_SYNC.SYNC_STATUS IS '[CHECK] 동기화 상태 PENDING/SUCCESS/FAIL'")

    # ── TB_AGENT_SYSTEM_ACCESS ───────────────────────────────
    op.execute("""
        CREATE TABLE TB_AGENT_SYSTEM_ACCESS (
            ACCESS_ID     VARCHAR2(36)   NOT NULL,
            USER_ID       VARCHAR2(50)   NOT NULL,
            GRANT_YN      CHAR(1)        DEFAULT 'Y' NOT NULL
                            CONSTRAINT CK_ACCESS_GRANT CHECK (GRANT_YN IN ('Y','N')),
            GRANT_REASON  VARCHAR2(500),
            GRANT_DT      DATE           DEFAULT SYSDATE NOT NULL,
            EXPIRE_DT     DATE,
            SYNC_DT       DATE,
            SYNC_STATUS   VARCHAR2(20)   DEFAULT 'PENDING' NOT NULL
                            CONSTRAINT CK_ACCESS_SYNC_STATUS
                            CHECK (SYNC_STATUS IN ('PENDING','SUCCESS','FAIL')),
            REG_DT        DATE           DEFAULT SYSDATE NOT NULL,
            UPD_DT        DATE,
            CONSTRAINT PK_AGENT_SYSTEM_ACCESS PRIMARY KEY (ACCESS_ID),
            CONSTRAINT FK_ACCESS_USER FOREIGN KEY (USER_ID) REFERENCES TB_USER_SYNC(USER_ID)
        )
    """)
    op.execute("COMMENT ON TABLE TB_AGENT_SYSTEM_ACCESS IS 'Agent 시스템 접근 권한 (외부 동기화)'")
    op.execute("COMMENT ON COLUMN TB_AGENT_SYSTEM_ACCESS.ACCESS_ID IS '접근권한 ID (PK) - UUID'")

    # ── TB_USER_PERMISSION ───────────────────────────────────
    op.execute("""
        CREATE TABLE TB_USER_PERMISSION (
            USER_PERMISSION_ID  VARCHAR2(36)   NOT NULL,
            USER_ID             VARCHAR2(50)   NOT NULL,
            PERMISSION_CD       VARCHAR2(20)   NOT NULL
                                  CONSTRAINT CK_PERM_CD CHECK (PERMISSION_CD IN ('ADMIN')),
            USE_YN              CHAR(1)        DEFAULT 'Y' NOT NULL
                                  CONSTRAINT CK_PERM_USE CHECK (USE_YN IN ('Y','N')),
            REG_DT              DATE           DEFAULT SYSDATE NOT NULL,
            REG_USER_ID         VARCHAR2(50)   NOT NULL,
            UPD_DT              DATE,
            UPD_USER_ID         VARCHAR2(50),
            CONSTRAINT PK_USER_PERMISSION PRIMARY KEY (USER_PERMISSION_ID),
            CONSTRAINT FK_PERM_USER FOREIGN KEY (USER_ID) REFERENCES TB_USER_SYNC(USER_ID)
        )
    """)
    op.execute("COMMENT ON TABLE TB_USER_PERMISSION IS 'Admin 내부 권한 (내부 관리 전용)'")
    op.execute("COMMENT ON COLUMN TB_USER_PERMISSION.USER_PERMISSION_ID IS '권한 ID (PK) - UUID'")

    # ── TB_CODE_GROUP ────────────────────────────────────────
    op.execute("""
        CREATE TABLE TB_CODE_GROUP (
            GROUP_CD     VARCHAR2(50)   NOT NULL,
            GROUP_NM     VARCHAR2(100)  NOT NULL,
            GROUP_DESC   VARCHAR2(500),
            USE_YN       CHAR(1)        DEFAULT 'Y' NOT NULL
                           CONSTRAINT CK_CGRP_USE CHECK (USE_YN IN ('Y','N')),
            REG_DT       DATE           DEFAULT SYSDATE NOT NULL,
            REG_USER_ID  VARCHAR2(50)   NOT NULL,
            UPD_DT       DATE,
            UPD_USER_ID  VARCHAR2(50),
            CONSTRAINT PK_CODE_GROUP PRIMARY KEY (GROUP_CD)
        )
    """)
    op.execute("COMMENT ON TABLE TB_CODE_GROUP IS '공통 코드 그룹 마스터'")

    # ── TB_CODE_DETAIL ───────────────────────────────────────
    op.execute("""
        CREATE TABLE TB_CODE_DETAIL (
            GROUP_CD     VARCHAR2(50)   NOT NULL,
            CODE_VAL     VARCHAR2(50)   NOT NULL,
            CODE_NM      VARCHAR2(100)  NOT NULL,
            CODE_DESC    VARCHAR2(500),
            SORT_ORDER   NUMBER         NOT NULL,
            USE_YN       CHAR(1)        DEFAULT 'Y' NOT NULL
                           CONSTRAINT CK_CDET_USE CHECK (USE_YN IN ('Y','N')),
            REG_DT       DATE           DEFAULT SYSDATE NOT NULL,
            REG_USER_ID  VARCHAR2(50)   NOT NULL,
            UPD_DT       DATE,
            UPD_USER_ID  VARCHAR2(50),
            CONSTRAINT PK_CODE_DETAIL PRIMARY KEY (GROUP_CD, CODE_VAL),
            CONSTRAINT FK_DETAIL_GROUP FOREIGN KEY (GROUP_CD) REFERENCES TB_CODE_GROUP(GROUP_CD)
        )
    """)
    op.execute("COMMENT ON TABLE TB_CODE_DETAIL IS '공통 코드 상세 (UI 드롭다운·라벨에 직접 사용)'")

    # ── TB_AGENT ─────────────────────────────────────────────
    op.execute("""
        CREATE TABLE TB_AGENT (
            AGENT_ID         VARCHAR2(36)    NOT NULL,
            AGENT_NM         VARCHAR2(200)   NOT NULL,
            AGENT_DESC       CLOB,
            AGENT_STATUS_CD  VARCHAR2(20)    DEFAULT 'PENDING' NOT NULL
                               CONSTRAINT CK_AGENT_STATUS
                               CHECK (AGENT_STATUS_CD IN ('PENDING','REJECTED','DEV','OPEN','DELETE_PENDING')),
            OWNER_USER_ID    VARCHAR2(50)    NOT NULL,
            DEL_YN           CHAR(1)         DEFAULT 'N' NOT NULL
                               CONSTRAINT CK_AGENT_DEL CHECK (DEL_YN IN ('Y','N')),
            DEL_DT           DATE,
            DEL_USER_ID      VARCHAR2(50),
            REG_DT           DATE            DEFAULT SYSDATE NOT NULL,
            UPD_DT           DATE,
            REG_USER_ID      VARCHAR2(50)    NOT NULL,
            UPD_USER_ID      VARCHAR2(50),
            CONSTRAINT PK_AGENT PRIMARY KEY (AGENT_ID),
            CONSTRAINT FK_AGENT_OWNER FOREIGN KEY (OWNER_USER_ID) REFERENCES TB_USER_SYNC(USER_ID)
        )
    """)
    op.execute("COMMENT ON TABLE TB_AGENT IS 'Agent 카드 (핵심)'")
    op.execute("COMMENT ON COLUMN TB_AGENT.AGENT_ID IS 'Agent ID (PK) - UUID'")
    op.execute("COMMENT ON COLUMN TB_AGENT.AGENT_STATUS_CD IS '[CODE_TABLE] 상태 코드 - TB_CODE_DETAIL(AGENT_STATUS_CD) 참조'")
    op.execute("COMMENT ON COLUMN TB_AGENT.DEL_YN IS '[CHECK] 소프트 삭제 여부 Y/N'")

    # ── TB_AGENT_MEMBER ──────────────────────────────────────
    op.execute("""
        CREATE TABLE TB_AGENT_MEMBER (
            AGENT_MEMBER_ID  VARCHAR2(36)   NOT NULL,
            AGENT_ID         VARCHAR2(36)   NOT NULL,
            USER_ID          VARCHAR2(50)   NOT NULL,
            ROLE_CD          VARCHAR2(20)   NOT NULL
                               CONSTRAINT CK_MEMBER_ROLE
                               CHECK (ROLE_CD IN ('AGENT_OWNER','AGENT_DEV')),
            USE_YN           CHAR(1)        DEFAULT 'Y' NOT NULL
                               CONSTRAINT CK_MEMBER_USE CHECK (USE_YN IN ('Y','N')),
            REG_DT           DATE           DEFAULT SYSDATE NOT NULL,
            UPD_DT           DATE,
            REG_USER_ID      VARCHAR2(50)   NOT NULL,
            UPD_USER_ID      VARCHAR2(50),
            CONSTRAINT PK_AGENT_MEMBER PRIMARY KEY (AGENT_MEMBER_ID),
            CONSTRAINT FK_MEMBER_AGENT FOREIGN KEY (AGENT_ID)  REFERENCES TB_AGENT(AGENT_ID),
            CONSTRAINT FK_MEMBER_USER  FOREIGN KEY (USER_ID)   REFERENCES TB_USER_SYNC(USER_ID),
            CONSTRAINT UQ_AGENT_MEMBER UNIQUE (AGENT_ID, USER_ID)
        )
    """)
    op.execute("COMMENT ON TABLE TB_AGENT_MEMBER IS 'Agent 구성원 권한 (Owner/Dev)'")
    op.execute("COMMENT ON COLUMN TB_AGENT_MEMBER.AGENT_MEMBER_ID IS '구성원 ID (PK) - UUID'")

    # ── TB_CONSENT_ITEM ──────────────────────────────────────
    op.execute("""
        CREATE TABLE TB_CONSENT_ITEM (
            CONSENT_ITEM_ID  VARCHAR2(36)    NOT NULL,
            ITEM_NM          VARCHAR2(200)   NOT NULL,
            ITEM_DESC        VARCHAR2(1000),
            SORT_ORDER       NUMBER          NOT NULL,
            REQUIRED_YN      CHAR(1)         DEFAULT 'Y' NOT NULL
                               CONSTRAINT CK_CONSENT_REQ CHECK (REQUIRED_YN IN ('Y','N')),
            USE_YN           CHAR(1)         DEFAULT 'Y' NOT NULL
                               CONSTRAINT CK_CONSENT_USE CHECK (USE_YN IN ('Y','N')),
            REG_DT           DATE            DEFAULT SYSDATE NOT NULL,
            CONSTRAINT PK_CONSENT_ITEM PRIMARY KEY (CONSENT_ITEM_ID)
        )
    """)
    op.execute("COMMENT ON TABLE TB_CONSENT_ITEM IS '개인정보 동의 항목 마스터 (10개)'")
    op.execute("COMMENT ON COLUMN TB_CONSENT_ITEM.CONSENT_ITEM_ID IS '동의항목 ID (PK) - UUID'")

    # ── TB_AGENT_CONSENT ─────────────────────────────────────
    op.execute("""
        CREATE TABLE TB_AGENT_CONSENT (
            AGENT_CONSENT_ID  VARCHAR2(36)    NOT NULL,
            AGENT_ID          VARCHAR2(36)    NOT NULL,
            CONSENT_ITEM_ID   VARCHAR2(36)    NOT NULL,
            AGREE_YN          CHAR(1)         NOT NULL
                                CONSTRAINT CK_AGREE_YN CHECK (AGREE_YN IN ('Y','N')),
            AGREE_DT          DATE            DEFAULT SYSDATE NOT NULL,
            USER_ID           VARCHAR2(50)    NOT NULL,
            CONSTRAINT PK_AGENT_CONSENT PRIMARY KEY (AGENT_CONSENT_ID),
            CONSTRAINT FK_CONSENT_AGENT  FOREIGN KEY (AGENT_ID)        REFERENCES TB_AGENT(AGENT_ID),
            CONSTRAINT FK_CONSENT_ITEM   FOREIGN KEY (CONSENT_ITEM_ID) REFERENCES TB_CONSENT_ITEM(CONSENT_ITEM_ID),
            CONSTRAINT FK_CONSENT_USER   FOREIGN KEY (USER_ID)         REFERENCES TB_USER_SYNC(USER_ID),
            CONSTRAINT UQ_AGENT_CONSENT  UNIQUE (AGENT_ID, CONSENT_ITEM_ID)
        )
    """)
    op.execute("COMMENT ON TABLE TB_AGENT_CONSENT IS 'Agent 신청 동의 내역'")
    op.execute("COMMENT ON COLUMN TB_AGENT_CONSENT.AGENT_CONSENT_ID IS '동의 ID (PK) - UUID'")

    # ── TB_APPROVAL_REQUEST ──────────────────────────────────
    op.execute("""
        CREATE TABLE TB_APPROVAL_REQUEST (
            APPROVAL_REQ_ID  VARCHAR2(36)    NOT NULL,
            AGENT_ID         VARCHAR2(36)    NOT NULL,
            REQ_TYPE_CD      VARCHAR2(20)    NOT NULL
                               CONSTRAINT CK_REQ_TYPE CHECK (REQ_TYPE_CD IN ('CREATE','DELETE')),
            REQ_STATUS_CD    VARCHAR2(20)    DEFAULT 'PENDING' NOT NULL
                               CONSTRAINT CK_REQ_STATUS
                               CHECK (REQ_STATUS_CD IN ('PENDING','APPROVED','REJECTED')),
            REQ_USER_ID      VARCHAR2(50)    NOT NULL,
            REQ_DT           DATE            DEFAULT SYSDATE NOT NULL,
            PROCESS_USER_ID  VARCHAR2(50),
            PROCESS_DT       DATE,
            REJECT_REASON    CLOB,
            REG_DT           DATE            DEFAULT SYSDATE NOT NULL,
            CONSTRAINT PK_APPROVAL_REQUEST  PRIMARY KEY (APPROVAL_REQ_ID),
            CONSTRAINT FK_APPR_AGENT        FOREIGN KEY (AGENT_ID)        REFERENCES TB_AGENT(AGENT_ID),
            CONSTRAINT FK_APPR_REQ_USER     FOREIGN KEY (REQ_USER_ID)     REFERENCES TB_USER_SYNC(USER_ID),
            CONSTRAINT FK_APPR_PROC_USER    FOREIGN KEY (PROCESS_USER_ID) REFERENCES TB_USER_SYNC(USER_ID)
        )
    """)
    op.execute("COMMENT ON TABLE TB_APPROVAL_REQUEST IS '승인 요청 관리 (생성/삭제)'")
    op.execute("COMMENT ON COLUMN TB_APPROVAL_REQUEST.APPROVAL_REQ_ID IS '승인요청 ID (PK) - UUID'")

    # ── TB_AGENT_HISTORY ─────────────────────────────────────
    op.execute("""
        CREATE TABLE TB_AGENT_HISTORY (
            HISTORY_ID        VARCHAR2(36)    NOT NULL,
            AGENT_ID          VARCHAR2(36)    NOT NULL,
            CHANGE_TYPE_CD    VARCHAR2(30)    NOT NULL
                                CONSTRAINT CK_HIST_TYPE
                                CHECK (CHANGE_TYPE_CD IN ('CREATE','UPDATE','STATUS_CHANGE','DELETE_REQ','DELETE')),
            BEFORE_STATUS_CD  VARCHAR2(20),
            AFTER_STATUS_CD   VARCHAR2(20),
            BEFORE_AGENT_NM   VARCHAR2(200),
            AFTER_AGENT_NM    VARCHAR2(200),
            BEFORE_AGENT_DESC CLOB,
            AFTER_AGENT_DESC  CLOB,
            APPROVAL_REQ_ID   VARCHAR2(36),
            REG_DT            DATE            DEFAULT SYSDATE NOT NULL,
            REG_USER_ID       VARCHAR2(50)    NOT NULL,
            CONSTRAINT PK_AGENT_HISTORY  PRIMARY KEY (HISTORY_ID),
            CONSTRAINT FK_HIST_AGENT     FOREIGN KEY (AGENT_ID)        REFERENCES TB_AGENT(AGENT_ID),
            CONSTRAINT FK_HIST_APPR      FOREIGN KEY (APPROVAL_REQ_ID) REFERENCES TB_APPROVAL_REQUEST(APPROVAL_REQ_ID)
        )
    """)
    op.execute("COMMENT ON TABLE TB_AGENT_HISTORY IS 'Agent 변경 이력 (전체 보존)'")
    op.execute("COMMENT ON COLUMN TB_AGENT_HISTORY.HISTORY_ID IS '이력 ID (PK) - UUID'")

    # ── 인덱스 생성 ───────────────────────────────────────────
    op.execute("CREATE INDEX IDX_USER_SYNC_EXT      ON TB_USER_SYNC            (EXT_SYSTEM_ID, SYNC_STATUS)")
    op.execute("CREATE INDEX IDX_ACCESS_USER        ON TB_AGENT_SYSTEM_ACCESS  (USER_ID, GRANT_YN, EXPIRE_DT)")
    op.execute("CREATE INDEX IDX_ACCESS_SYNC        ON TB_AGENT_SYSTEM_ACCESS  (SYNC_STATUS, SYNC_DT)")
    op.execute("CREATE INDEX IDX_USER_PERM_USER     ON TB_USER_PERMISSION      (USER_ID, USE_YN)")
    op.execute("CREATE INDEX IDX_AGENT_OWNER        ON TB_AGENT                (OWNER_USER_ID, DEL_YN)")
    op.execute("CREATE INDEX IDX_AGENT_STATUS       ON TB_AGENT                (AGENT_STATUS_CD, DEL_YN)")
    op.execute("CREATE INDEX IDX_AGENT_MEMBER_USER  ON TB_AGENT_MEMBER         (USER_ID, USE_YN)")
    op.execute("CREATE INDEX IDX_AGENT_MEMBER_AGENT ON TB_AGENT_MEMBER         (AGENT_ID, USE_YN)")
    op.execute("CREATE INDEX IDX_CONSENT_AGENT      ON TB_AGENT_CONSENT        (AGENT_ID)")
    op.execute("CREATE INDEX IDX_APPROVAL_STATUS    ON TB_APPROVAL_REQUEST     (REQ_STATUS_CD, REQ_TYPE_CD)")
    op.execute("CREATE INDEX IDX_APPROVAL_AGENT     ON TB_APPROVAL_REQUEST     (AGENT_ID, REQ_STATUS_CD)")
    op.execute("CREATE INDEX IDX_CODE_DETAIL_USE    ON TB_CODE_DETAIL          (GROUP_CD, USE_YN)")
    op.execute("CREATE INDEX IDX_HISTORY_AGENT      ON TB_AGENT_HISTORY        (AGENT_ID, REG_DT)")

    # ── 초기 코드 그룹 데이터 ────────────────────────────────
    op.execute("""
        INSERT INTO TB_CODE_GROUP (GROUP_CD, GROUP_NM, GROUP_DESC, REG_USER_ID)
        VALUES ('AGENT_STATUS_CD', 'Agent 상태 코드', 'Agent 카드 상태를 관리하는 코드 그룹', 'SYSTEM')
    """)
    op.execute("""
        INSERT INTO TB_CODE_GROUP (GROUP_CD, GROUP_NM, GROUP_DESC, REG_USER_ID)
        VALUES ('ROLE_CD', '역할 코드', 'Agent 구성원 역할 코드 그룹', 'SYSTEM')
    """)
    op.execute("""
        INSERT INTO TB_CODE_GROUP (GROUP_CD, GROUP_NM, GROUP_DESC, REG_USER_ID)
        VALUES ('REQ_TYPE_CD', '승인 요청 유형 코드', '승인 요청 유형 코드 그룹', 'SYSTEM')
    """)
    op.execute("""
        INSERT INTO TB_CODE_GROUP (GROUP_CD, GROUP_NM, GROUP_DESC, REG_USER_ID)
        VALUES ('REQ_STATUS_CD', '승인 처리 상태 코드', '승인 처리 상태 코드 그룹', 'SYSTEM')
    """)

    # ── 초기 코드 상세 데이터 ────────────────────────────────
    # AGENT_STATUS_CD
    op.execute("INSERT INTO TB_CODE_DETAIL (GROUP_CD,CODE_VAL,CODE_NM,SORT_ORDER,REG_USER_ID) VALUES ('AGENT_STATUS_CD','PENDING','승인대기',1,'SYSTEM')")
    op.execute("INSERT INTO TB_CODE_DETAIL (GROUP_CD,CODE_VAL,CODE_NM,SORT_ORDER,REG_USER_ID) VALUES ('AGENT_STATUS_CD','REJECTED','반려',2,'SYSTEM')")
    op.execute("INSERT INTO TB_CODE_DETAIL (GROUP_CD,CODE_VAL,CODE_NM,SORT_ORDER,REG_USER_ID) VALUES ('AGENT_STATUS_CD','DEV','Dev',3,'SYSTEM')")
    op.execute("INSERT INTO TB_CODE_DETAIL (GROUP_CD,CODE_VAL,CODE_NM,SORT_ORDER,REG_USER_ID) VALUES ('AGENT_STATUS_CD','OPEN','Open',4,'SYSTEM')")
    op.execute("INSERT INTO TB_CODE_DETAIL (GROUP_CD,CODE_VAL,CODE_NM,SORT_ORDER,REG_USER_ID) VALUES ('AGENT_STATUS_CD','DELETE_PENDING','삭제승인대기',5,'SYSTEM')")

    # ROLE_CD
    op.execute("INSERT INTO TB_CODE_DETAIL (GROUP_CD,CODE_VAL,CODE_NM,SORT_ORDER,REG_USER_ID) VALUES ('ROLE_CD','AGENT_OWNER','Agent Owner',1,'SYSTEM')")
    op.execute("INSERT INTO TB_CODE_DETAIL (GROUP_CD,CODE_VAL,CODE_NM,SORT_ORDER,REG_USER_ID) VALUES ('ROLE_CD','AGENT_DEV','Agent 개발자',2,'SYSTEM')")

    # REQ_TYPE_CD
    op.execute("INSERT INTO TB_CODE_DETAIL (GROUP_CD,CODE_VAL,CODE_NM,SORT_ORDER,REG_USER_ID) VALUES ('REQ_TYPE_CD','CREATE','생성 요청',1,'SYSTEM')")
    op.execute("INSERT INTO TB_CODE_DETAIL (GROUP_CD,CODE_VAL,CODE_NM,SORT_ORDER,REG_USER_ID) VALUES ('REQ_TYPE_CD','DELETE','삭제 요청',2,'SYSTEM')")

    # REQ_STATUS_CD
    op.execute("INSERT INTO TB_CODE_DETAIL (GROUP_CD,CODE_VAL,CODE_NM,SORT_ORDER,REG_USER_ID) VALUES ('REQ_STATUS_CD','PENDING','처리대기',1,'SYSTEM')")
    op.execute("INSERT INTO TB_CODE_DETAIL (GROUP_CD,CODE_VAL,CODE_NM,SORT_ORDER,REG_USER_ID) VALUES ('REQ_STATUS_CD','APPROVED','승인',2,'SYSTEM')")
    op.execute("INSERT INTO TB_CODE_DETAIL (GROUP_CD,CODE_VAL,CODE_NM,SORT_ORDER,REG_USER_ID) VALUES ('REQ_STATUS_CD','REJECTED','반려',3,'SYSTEM')")

    # ── 초기 동의 항목 데이터 (10개) ─────────────────────────
    import uuid
    consent_items = [
        ("개인정보 수집·이용 동의", "성명, 이메일, 부서명 등 기본 정보 수집 동의", 1),
        ("개인정보 제3자 제공 동의", "Agent 운영을 위한 관련 팀 정보 제공 동의", 2),
        ("민감정보 처리 동의", "업무 관련 민감 정보 처리 동의", 3),
        ("개인정보 국외 이전 동의", "해외 클라우드 서비스 이용 관련 정보 이전 동의", 4),
        ("마케팅 활용 동의", "Agent 관련 마케팅 정보 수신 동의", 5),
        ("서비스 개선을 위한 데이터 활용 동의", "서비스 품질 향상을 위한 데이터 분석 동의", 6),
        ("로그 데이터 수집 동의", "Agent 사용 로그 수집 및 분석 동의", 7),
        ("알림 서비스 이용 동의", "승인 상태 변경 등 시스템 알림 수신 동의", 8),
        ("보안 정책 준수 서약", "사내 보안 정책 및 개인정보보호법 준수 서약", 9),
        ("이용약관 동의", "Agent System 이용약관 전체 동의", 10),
    ]
    for nm, desc, order in consent_items:
        item_id = str(uuid.uuid4())
        op.execute(
            f"INSERT INTO TB_CONSENT_ITEM (CONSENT_ITEM_ID,ITEM_NM,ITEM_DESC,SORT_ORDER,REQUIRED_YN,USE_YN) "
            f"VALUES ('{item_id}','{nm}','{desc}',{order},'Y','Y')"
        )


def downgrade() -> None:
    """테이블 전체 삭제 (역순)"""
    tables = [
        "TB_AGENT_HISTORY",
        "TB_APPROVAL_REQUEST",
        "TB_AGENT_CONSENT",
        "TB_CONSENT_ITEM",
        "TB_AGENT_MEMBER",
        "TB_AGENT",
        "TB_CODE_DETAIL",
        "TB_CODE_GROUP",
        "TB_USER_PERMISSION",
        "TB_AGENT_SYSTEM_ACCESS",
        "TB_USER_SYNC",
    ]
    for table in tables:
        op.execute(f"DROP TABLE {table} CASCADE CONSTRAINTS PURGE")
