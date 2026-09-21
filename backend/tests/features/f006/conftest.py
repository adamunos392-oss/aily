"""F-006 独立测试库。禁止 drop 运行时业务库。"""

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.api.deps import get_db
from src.db.seed import seed_database
from src.db.session import DATABASE_FILE, create_all_tables, create_engine, sqlite_url_for
from src.main import app

EXPECTED_CASE_IDS = [
    "eval-qa-travel",
    "eval-qa-refuse",
    "eval-meeting-success",
    "eval-meeting-timeout",
    "eval-meeting-stale",
    "eval-report",
    "eval-rooms",
]


@pytest.fixture
async def f006_engine(tmp_path: Path) -> AsyncGenerator[AsyncEngine, None]:
    db_file = tmp_path / "aily-f006.db"
    assert db_file.resolve() != DATABASE_FILE.resolve()
    engine = create_engine(sqlite_url_for(db_file))
    await create_all_tables(engine)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
def f006_session_maker(f006_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        f006_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@pytest.fixture
async def client(
    f006_session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[TestClient, None]:
    async with f006_session_maker() as session:
        await seed_database(session)
        await session.commit()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with f006_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def assert_envelope_ok(body: object) -> dict[str, Any]:
    assert isinstance(body, dict)
    assert body["code"] == 200
    assert body["message"] == "ok"
    assert body["data"] is not None
    data = body["data"]
    assert isinstance(data, dict)
    return cast(dict[str, Any], data)
