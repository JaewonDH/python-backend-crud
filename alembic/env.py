"""
Alembic 환경 설정
- app/domains/ 하위 모든 도메인 모델 import 후 target_metadata 설정
- Oracle 동기 엔진 사용
"""
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Alembic Config 객체
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── 모든 도메인 모델 import (Base.metadata 수집) ──
from app.models.base import Base              # noqa: E402
import app.domains.user.models               # noqa: E402, F401
import app.domains.common.models             # noqa: E402, F401
import app.domains.agent.models              # noqa: E402, F401
import app.domains.approval.models           # noqa: E402, F401

target_metadata = Base.metadata

# .env 기반 DB URL 오버라이드
from app.core.config import settings         # noqa: E402
config.set_main_option("sqlalchemy.url", settings.sync_database_url)


def run_migrations_offline() -> None:
    """오프라인 모드: SQL 스크립트 생성"""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """온라인 모드: 직접 DB 실행"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
