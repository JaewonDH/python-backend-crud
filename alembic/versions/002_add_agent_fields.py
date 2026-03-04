"""TB_AGENT 신청 필드 추가 및 그룹1/그룹2 코드 등록

001_initial 이 이미 적용된 환경에서 다음을 수행:
  1. TB_AGENT 에 신청 입력 컬럼 추가
     - TASK_NO (과제번호), TEAM_NM (팀이름), CHARGE_NM (담당)
     - EMP_NO (사번), EMP_NM (이름)
     - GROUP1_CD (그룹1 단일선택), GROUP2_CD (그룹2 단일선택)
  2. TB_CODE_GROUP 에 GROUP1_CD / GROUP2_CD 그룹 등록
  3. TB_CODE_DETAIL 에 그룹1/그룹2 선택 옵션 등록

Revision ID: 002
Revises: 001
Create Date: 2026-03-04
"""
from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """TB_AGENT 신규 컬럼 추가 + 그룹 코드 데이터 등록"""

    # ── TB_AGENT 컬럼 추가 ────────────────────────────────────
    op.execute("ALTER TABLE TB_AGENT ADD TASK_NO VARCHAR2(100)")
    op.execute("ALTER TABLE TB_AGENT ADD TEAM_NM VARCHAR2(200)")
    op.execute("ALTER TABLE TB_AGENT ADD CHARGE_NM VARCHAR2(200)")
    op.execute("ALTER TABLE TB_AGENT ADD EMP_NO VARCHAR2(50)")
    op.execute("ALTER TABLE TB_AGENT ADD EMP_NM VARCHAR2(100)")
    op.execute("ALTER TABLE TB_AGENT ADD GROUP1_CD VARCHAR2(50)")
    op.execute("ALTER TABLE TB_AGENT ADD GROUP2_CD VARCHAR2(50)")

    # 컬럼 코멘트
    op.execute("COMMENT ON COLUMN TB_AGENT.TASK_NO IS '과제번호'")
    op.execute("COMMENT ON COLUMN TB_AGENT.TEAM_NM IS '팀이름'")
    op.execute("COMMENT ON COLUMN TB_AGENT.CHARGE_NM IS '담당'")
    op.execute("COMMENT ON COLUMN TB_AGENT.EMP_NO IS '사번'")
    op.execute("COMMENT ON COLUMN TB_AGENT.EMP_NM IS '이름'")
    op.execute("COMMENT ON COLUMN TB_AGENT.GROUP1_CD IS '[CODE_TABLE] 그룹1 단일선택 코드 - TB_CODE_DETAIL(GROUP1_CD) 참조'")
    op.execute("COMMENT ON COLUMN TB_AGENT.GROUP2_CD IS '[CODE_TABLE] 그룹2 단일선택 코드 - TB_CODE_DETAIL(GROUP2_CD) 참조'")

    # ── 그룹 코드 마스터 등록 ────────────────────────────────
    op.execute("""
        INSERT INTO TB_CODE_GROUP (GROUP_CD, GROUP_NM, GROUP_DESC, REG_USER_ID)
        VALUES ('GROUP1_CD', '그룹1', 'Agent 신청 시 그룹1 선택 옵션', 'SYSTEM')
    """)
    op.execute("""
        INSERT INTO TB_CODE_GROUP (GROUP_CD, GROUP_NM, GROUP_DESC, REG_USER_ID)
        VALUES ('GROUP2_CD', '그룹2', 'Agent 신청 시 그룹2 선택 옵션', 'SYSTEM')
    """)

    # ── GROUP1_CD 선택 옵션 ──────────────────────────────────
    op.execute("INSERT INTO TB_CODE_DETAIL (GROUP_CD,CODE_VAL,CODE_NM,SORT_ORDER,REG_USER_ID) VALUES ('GROUP1_CD','GRP1_A','그룹A',1,'SYSTEM')")
    op.execute("INSERT INTO TB_CODE_DETAIL (GROUP_CD,CODE_VAL,CODE_NM,SORT_ORDER,REG_USER_ID) VALUES ('GROUP1_CD','GRP1_B','그룹B',2,'SYSTEM')")
    op.execute("INSERT INTO TB_CODE_DETAIL (GROUP_CD,CODE_VAL,CODE_NM,SORT_ORDER,REG_USER_ID) VALUES ('GROUP1_CD','GRP1_C','그룹C',3,'SYSTEM')")

    # ── GROUP2_CD 선택 옵션 ──────────────────────────────────
    op.execute("INSERT INTO TB_CODE_DETAIL (GROUP_CD,CODE_VAL,CODE_NM,SORT_ORDER,REG_USER_ID) VALUES ('GROUP2_CD','GRP2_X','유형X',1,'SYSTEM')")
    op.execute("INSERT INTO TB_CODE_DETAIL (GROUP_CD,CODE_VAL,CODE_NM,SORT_ORDER,REG_USER_ID) VALUES ('GROUP2_CD','GRP2_Y','유형Y',2,'SYSTEM')")
    op.execute("INSERT INTO TB_CODE_DETAIL (GROUP_CD,CODE_VAL,CODE_NM,SORT_ORDER,REG_USER_ID) VALUES ('GROUP2_CD','GRP2_Z','유형Z',3,'SYSTEM')")


def downgrade() -> None:
    """추가한 컬럼 및 코드 데이터 롤백"""

    # 그룹 코드 상세 삭제
    op.execute("DELETE FROM TB_CODE_DETAIL WHERE GROUP_CD IN ('GROUP1_CD', 'GROUP2_CD')")

    # 그룹 코드 마스터 삭제
    op.execute("DELETE FROM TB_CODE_GROUP WHERE GROUP_CD IN ('GROUP1_CD', 'GROUP2_CD')")

    # TB_AGENT 컬럼 삭제 (Oracle: DROP COLUMN)
    op.execute("ALTER TABLE TB_AGENT DROP COLUMN GROUP2_CD")
    op.execute("ALTER TABLE TB_AGENT DROP COLUMN GROUP1_CD")
    op.execute("ALTER TABLE TB_AGENT DROP COLUMN EMP_NM")
    op.execute("ALTER TABLE TB_AGENT DROP COLUMN EMP_NO")
    op.execute("ALTER TABLE TB_AGENT DROP COLUMN CHARGE_NM")
    op.execute("ALTER TABLE TB_AGENT DROP COLUMN TEAM_NM")
    op.execute("ALTER TABLE TB_AGENT DROP COLUMN TASK_NO")
