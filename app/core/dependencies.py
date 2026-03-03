"""
공통 의존성 (페이지네이션 등)
"""
from fastapi import Query


class Pagination:
    """페이지네이션 파라미터"""
    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="페이지 번호 (1부터 시작)"),
        size: int = Query(default=20, ge=1, le=100, description="페이지당 항목 수"),
    ):
        self.page = page
        self.size = size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size
