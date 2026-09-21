"""F-004 独立测试库。禁止 drop 运行时业务库。"""

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

REPORT_QUERY = "帮我生成本周周报"
WORK_FACT_ARCH = "完成 Aily 工作台信息架构评审"
WORK_FACT_REVIEW = "与张明对齐项目复盘会材料"
CHITCHAT = "晚上吃啥"


@pytest.fixture
async def f004_engine(tmp_path: Path) -> AsyncGenerator[AsyncEngine, None]:
    db_file = tmp_path / "aily-f004.db"
    assert db_file.resolve() != DATABASE_FILE.resolve()
    engine = create_engine(sqlite_url_for(db_file))
    await create_all_tables(engine)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
def f004_session_maker(f004_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        f004_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@pytest.fixture
async def client(
    f004_session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[TestClient, None]:
    async with f004_session_maker() as session:
        await seed_database(session)
        await session.commit()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with f004_session_maker() as session:
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


def create_owned_conversation(client: TestClient) -> str:
    response = client.post("/api/conversations", json={"title": None})
    data = assert_envelope_ok(response.json())
    conversation_id = data["conversation_id"]
    assert isinstance(conversation_id, str)
    return conversation_id


def post_report_turn(
    client: TestClient,
    conversation_id: str,
    *,
    content: str = REPORT_QUERY,
    entry_source: str = "manual",
) -> dict[str, Any]:
    response = client.post(
        f"/api/conversations/{conversation_id}/turns",
        json={
            "content": content,
            "entry_source": entry_source,
            "choice_id": None,
            "client_turn_key": None,
        },
    )
    assert response.status_code == 200, response.text
    return assert_envelope_ok(response.json())
