### 4. 서버 실행

```bash
# 기본 실행 (핫 리로드)
uv run uvicorn app.main:app --reload

# 포트 변경
uv run uvicorn app.main:app --reload --port 8080

# 외부 접속 허용
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. API 문서 확인

| URL | 설명 |
|-----|------|
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/health | 서버 상태 확인 |

---

## DB 마이그레이션 (Alembic)

### 초기 테이블 생성

```bash
uv run alembic upgrade head
```

성공 시 출력:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001, initial table creation
```


### 현재 마이그레이션 상태 확인

```bash
uv run alembic current
```

### 마이그레이션 이력 조회

```bash
uv run alembic history --verbose
```

### 테이블 전체 삭제

```bash
uv run alembic downgrade base
```

> 모든 테이블과 데이터가 삭제됩니다. 실행 전 반드시 확인하세요.

### 테이블 재생성 (삭제 후 재생성)

```bash
uv run alembic downgrade base && uv run alembic upgrade head
```

### 특정 버전으로 이동

```bash
# 버전 지정 업그레이드
uv run alembic upgrade 001

# 버전 지정 다운그레이드
uv run alembic downgrade 001

# 한 단계 롤백
uv run alembic downgrade -1
```

---
