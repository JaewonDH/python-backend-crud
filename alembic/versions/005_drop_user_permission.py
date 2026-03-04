"""TB_USER_PERMISSION 테이블 제거

004 이 적용된 환경에서 다음을 수행:
  1. TB_USER_PERMISSION 테이블 삭제
     - Admin 권한 체계를 TB_EXT_PERMISSION(AGENT_SYSTEM_ADMIN)으로 완전 대체
     - TB_AGENT_SYSTEM_ACCESS는 레거시로 유지 (인증 미사용)

권한 체계 변경:
  Before: TB_USER_PERMISSION(PERMISSION_CD='ADMIN') → Admin 체크
  After:  TB_USER_EXT_PERMISSION + TB_EXT_PERMISSION(PERMISSION_CD='AGENT_SYSTEM_ADMIN') → Admin 체크

Revision ID: 005
Revises: 004
Create Date: 2026-03-04
"""
from typing import Sequence, Union

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # TB_USER_PERMISSION 테이블 삭제 (AGENT_SYSTEM_ADMIN 권한으로 대체)
    op.execute("DROP TABLE TB_USER_PERMISSION CASCADE CONSTRAINTS PURGE")


def downgrade() -> None:
    # TB_USER_PERMISSION 복원
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
    op.execute("COMMENT ON TABLE TB_USER_PERMISSION IS 'Admin 내부 권한 (복원)'")
