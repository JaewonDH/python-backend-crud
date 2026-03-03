"""
애플리케이션 설정 관리 (pydantic-settings 기반)
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Oracle DB 설정
    oracle_host: str = "localhost"
    oracle_port: int = 1521
    oracle_service: str = "FREEPDB1"
    oracle_username: str = "myuser"
    oracle_password: str = "mypassword"

    # 앱 설정
    app_env: str = "development"
    app_debug: bool = True

    @property
    def sync_database_url(self) -> str:
        """동기 Oracle DB 접속 URL"""
        return (
            f"oracle+oracledb://{self.oracle_username}:{self.oracle_password}"
            f"@{self.oracle_host}:{self.oracle_port}"
            f"/?service_name={self.oracle_service}"
        )

    @property
    def async_database_url(self) -> str:
        """비동기 Oracle DB 접속 URL"""
        return (
            f"oracle+oracledb_async://{self.oracle_username}:{self.oracle_password}"
            f"@{self.oracle_host}:{self.oracle_port}"
            f"/?service_name={self.oracle_service}"
        )


# 전역 설정 인스턴스
settings = Settings()
