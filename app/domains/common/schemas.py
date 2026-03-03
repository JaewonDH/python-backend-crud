"""공통 코드 도메인 스키마 (Pydantic)"""
from datetime import datetime
from pydantic import BaseModel


# ── CodeGroup ──────────────────────────────────────
class CodeGroupCreate(BaseModel):
    """코드 그룹 생성 요청"""
    group_cd: str
    group_nm: str
    group_desc: str | None = None


class CodeGroupResponse(BaseModel):
    """코드 그룹 응답"""
    group_cd: str
    group_nm: str
    group_desc: str | None
    use_yn: str
    reg_dt: datetime

    model_config = {"from_attributes": True}


# ── CodeDetail ─────────────────────────────────────
class CodeDetailCreate(BaseModel):
    """코드 상세 생성 요청"""
    code_val: str
    code_nm: str
    code_desc: str | None = None
    sort_order: int


class CodeDetailResponse(BaseModel):
    """코드 상세 응답"""
    group_cd: str
    code_val: str
    code_nm: str
    code_desc: str | None
    sort_order: int
    use_yn: str
    reg_dt: datetime

    model_config = {"from_attributes": True}


# ── ConsentItem ────────────────────────────────────
# agent 도메인에서 이전 (경계 수정: 공통 마스터 데이터)
class ConsentItemCreate(BaseModel):
    """동의 항목 생성 요청"""
    item_nm: str
    item_desc: str | None = None
    sort_order: int
    required_yn: str = "Y"


class ConsentItemResponse(BaseModel):
    """동의 항목 응답"""
    consent_item_id: str
    item_nm: str
    item_desc: str | None
    sort_order: int
    required_yn: str
    use_yn: str
    reg_dt: datetime

    model_config = {"from_attributes": True}
