"""동의 항목 TEXT 타입 및 입력값 테이블 추가

002 가 이미 적용된 환경에서 다음을 수행:
  1. TB_CONSENT_ITEM 에 ITEM_TYPE_CD 컬럼 추가 (YN/TEXT)
  2. TB_AGENT_CONSENT.AGREE_YN NOT NULL → NULL 허용으로 변경
  3. 신규 테이블 TB_AGENT_CONSENT_VALUE 생성
     - TEXT 타입 동의 항목의 사용자 입력값을 여러 개 저장
  4. 기존 동의 항목 데이터 ITEM_TYPE_CD = 'YN' 으로 일괄 업데이트
  5. 9번 항목(활용 목적 입력)을 TEXT 타입으로 추가

Revision ID: 003
Revises: 002
Create Date: 2026-03-04
"""
from typing import Sequence, Union

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. TB_CONSENT_ITEM 에 ITEM_TYPE_CD 추가 ──────────────
    op.execute("ALTER TABLE TB_CONSENT_ITEM ADD ITEM_TYPE_CD VARCHAR2(10) DEFAULT 'YN' NOT NULL")
    op.execute("""
        ALTER TABLE TB_CONSENT_ITEM ADD CONSTRAINT CK_CONSENT_TYPE
        CHECK (ITEM_TYPE_CD IN ('YN','TEXT'))
    """)
    op.execute("COMMENT ON COLUMN TB_CONSENT_ITEM.ITEM_TYPE_CD IS '[CHECK] 항목 유형 YN(Y/N 선택) / TEXT(텍스트 다중 입력)'")

    # 기존 데이터 전체 YN 으로 업데이트 (DEFAULT 로 이미 'YN' 이지만 명시)
    op.execute("UPDATE TB_CONSENT_ITEM SET ITEM_TYPE_CD = 'YN'")

    # ── 2. TB_AGENT_CONSENT.AGREE_YN NULL 허용으로 변경 ──────
    # Oracle: 기존 CHECK 제약 삭제 후 재생성
    op.execute("ALTER TABLE TB_AGENT_CONSENT DROP CONSTRAINT CK_AGREE_YN")
    op.execute("ALTER TABLE TB_AGENT_CONSENT MODIFY AGREE_YN CHAR(1) NULL")
    op.execute("""
        ALTER TABLE TB_AGENT_CONSENT ADD CONSTRAINT CK_AGREE_YN
        CHECK (AGREE_YN IS NULL OR AGREE_YN IN ('Y','N'))
    """)
    op.execute("COMMENT ON COLUMN TB_AGENT_CONSENT.AGREE_YN IS 'YN 타입만 사용 (TEXT 타입은 NULL, 값은 TB_AGENT_CONSENT_VALUE 참조)'")

    # ── 3. TB_AGENT_CONSENT_VALUE 테이블 생성 ────────────────
    op.execute("""
        CREATE TABLE TB_AGENT_CONSENT_VALUE (
            CONSENT_VALUE_ID  VARCHAR2(36)    NOT NULL,
            AGENT_CONSENT_ID  VARCHAR2(36)    NOT NULL,
            TEXT_VALUE        VARCHAR2(2000)  NOT NULL,
            SORT_ORDER        NUMBER          NOT NULL,
            REG_DT            DATE            DEFAULT SYSDATE NOT NULL,
            CONSTRAINT PK_CONSENT_VALUE  PRIMARY KEY (CONSENT_VALUE_ID),
            CONSTRAINT FK_CVAL_CONSENT   FOREIGN KEY (AGENT_CONSENT_ID) REFERENCES TB_AGENT_CONSENT(AGENT_CONSENT_ID)
        )
    """)
    op.execute("COMMENT ON TABLE TB_AGENT_CONSENT_VALUE IS 'TEXT 타입 동의 항목의 사용자 입력값 (여러 개 저장)'")
    op.execute("COMMENT ON COLUMN TB_AGENT_CONSENT_VALUE.CONSENT_VALUE_ID IS '입력값 ID (PK) - UUID'")
    op.execute("COMMENT ON COLUMN TB_AGENT_CONSENT_VALUE.TEXT_VALUE IS '사용자 입력 텍스트'")
    op.execute("COMMENT ON COLUMN TB_AGENT_CONSENT_VALUE.SORT_ORDER IS '입력 순서'")
    op.execute("CREATE INDEX IDX_CONSENT_VALUE ON TB_AGENT_CONSENT_VALUE (AGENT_CONSENT_ID)")

    # ── 4. 기존 동의 항목 중 '보안 정책 준수 서약' → 활용 목적 입력(TEXT) 추가 ──
    import uuid
    item_id = str(uuid.uuid4())
    op.execute(
        f"INSERT INTO TB_CONSENT_ITEM "
        f"(CONSENT_ITEM_ID,ITEM_NM,ITEM_DESC,SORT_ORDER,ITEM_TYPE_CD,REQUIRED_YN,USE_YN) "
        f"VALUES ('{item_id}','활용 목적 입력',"
        f"'Agent를 활용하려는 목적을 자유롭게 작성 (여러 개 가능)',9,'TEXT','Y','Y')"
    )


def downgrade() -> None:
    # 추가한 TEXT 타입 항목 삭제 (이름 기준)
    op.execute("DELETE FROM TB_CONSENT_ITEM WHERE ITEM_NM = '활용 목적 입력' AND ITEM_TYPE_CD = 'TEXT'")

    # TB_AGENT_CONSENT_VALUE 테이블 삭제
    op.execute("DROP TABLE TB_AGENT_CONSENT_VALUE CASCADE CONSTRAINTS PURGE")

    # AGREE_YN NOT NULL 복원
    op.execute("ALTER TABLE TB_AGENT_CONSENT DROP CONSTRAINT CK_AGREE_YN")
    op.execute("ALTER TABLE TB_AGENT_CONSENT MODIFY AGREE_YN CHAR(1) NOT NULL")
    op.execute("""
        ALTER TABLE TB_AGENT_CONSENT ADD CONSTRAINT CK_AGREE_YN
        CHECK (AGREE_YN IN ('Y','N'))
    """)

    # ITEM_TYPE_CD 컬럼 삭제
    op.execute("ALTER TABLE TB_CONSENT_ITEM DROP CONSTRAINT CK_CONSENT_TYPE")
    op.execute("ALTER TABLE TB_CONSENT_ITEM DROP COLUMN ITEM_TYPE_CD")
