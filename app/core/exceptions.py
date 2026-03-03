"""
커스텀 HTTP 예외 정의
"""
from fastapi import HTTPException, status


class UnauthorizedException(HTTPException):
    """인증 실패 (401)"""
    def __init__(self, detail: str = "인증이 필요합니다."):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenException(HTTPException):
    """권한 없음 (403)"""
    def __init__(self, detail: str = "접근 권한이 없습니다."):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFoundException(HTTPException):
    """리소스 없음 (404)"""
    def __init__(self, detail: str = "리소스를 찾을 수 없습니다."):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictException(HTTPException):
    """중복/충돌 (409)"""
    def __init__(self, detail: str = "이미 존재하는 리소스입니다."):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class BadRequestException(HTTPException):
    """잘못된 요청 (400)"""
    def __init__(self, detail: str = "잘못된 요청입니다."):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
