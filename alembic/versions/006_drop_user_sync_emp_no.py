"""TB_USER_SYNC.EMP_NO 컬럼 제거

권한 체크를 EMP_NO(사번) 기반에서 USER_ID 기반으로 변경함에 따라
TB_USER_SYNC의 EMP_NO 컬럼이 불필요해짐.
NOTE: TB_AGENT.EMP_NO(담당자 사번)는 Agent 카드 신청 폼 필드이므로 유지.

Revision ID: 006
Revises: 005
Create Date: 2026-03-04
"""
from typing import Sequence, Union

from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 인덱스 먼저 삭제 후 컬럼 제거
    op.execute("DROP INDEX IDX_USER_SYNC_EMP_NO")
    op.execute("ALTER TABLE TB_USER_SYNC DROP COLUMN EMP_NO")


def downgrade() -> None:
    op.execute("ALTER TABLE TB_USER_SYNC ADD EMP_NO VARCHAR2(50)")
    op.execute("CREATE INDEX IDX_USER_SYNC_EMP_NO ON TB_USER_SYNC (EMP_NO)")
