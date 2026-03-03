"""
공통 응답 스키마
"""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """페이지네이션 응답 공통 구조"""
    items: list[T]
    total: int
    page: int
    size: int
    total_pages: int


class MessageResponse(BaseModel):
    """단순 메시지 응답"""
    message: str
