"""F-001 独立测试库。禁止 drop 运行时业务库。"""

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.api.deps import get_db
from src.db.models import Confirmation, Conversation, Turn
from src.db.seed import seed_database
from src.db.session import DATABASE_FILE, create_all_tables, create_engine, sqlite_url_for
from src.main import app


@pytest.fixture
async def f001_engine(tmp_path: Path) -> AsyncGenerator[AsyncEngine, None]:
    db_file = tmp_path / "aily-f001.db"
    assert db_file.resolve() != DATABASE_FILE.resolve()
    engine = create_engine(sqlite_url_for(db_file))
    await create_all_tables(engine)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
def f001_session_maker(f001_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        f001_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@pytest.fixture
async def client(
    f001_session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[TestClient, None]:
    async with f001_session_maker() as session:
        await seed_database(session)
        await session.commit()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with f001_session_maker() as session:
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


def assert_envelope_error(body: object, status_code: int, message: str) -> None:
    assert isinstance(body, dict)
    assert body["code"] == status_code
    assert body["message"] == message
    assert body["data"] is None


async def add_conversation(
    session: AsyncSession,
    *,
    conversation_id: str,
    user_id: str,
    title: str,
    preview: str | None = None,
    created_at: str = "2026-09-21T05:00:00Z",
    updated_at: str = "2026-09-21T06:00:00Z",
) -> Conversation:
    row = Conversation(
        conversation_id=conversation_id,
        user_id=user_id,
        title=title,
        preview=preview,
        created_at=created_at,
        updated_at=updated_at,
    )
    session.add(row)
    await session.flush()
    return row


async def add_turn(
    session: AsyncSession,
    *,
    turn_id: str,
    conversation_id: str,
    content: str,
    status: str = "awaiting_confirmation",
    slot_state_json: str | None = None,
    created_at: str = "2026-09-21T06:00:00Z",
) -> Turn:
    row = Turn(
        turn_id=turn_id,
        conversation_id=conversation_id,
        role="user",
        content=content,
        entry_source="manual",
        status=status,
        slot_state_json=slot_state_json,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(row)
    await session.flush()
    return row


async def add_pending_confirmation(
    session: AsyncSession,
    *,
    confirmation_id: str,
    conversation_id: str,
    turn_id: str,
    topic: str,
    meeting_time: str = "明天下午三点",
    attendees_json: str = '["张明"]',
    duration_minutes: int,
    meeting_type: str,
    slot_snapshot_hash: str,
    created_at: str = "2026-09-21T06:00:01Z",
) -> Confirmation:
    row = Confirmation(
        confirmation_id=confirmation_id,
        conversation_id=conversation_id,
        turn_id=turn_id,
        status="pending",
        meeting_time=meeting_time,
        attendees_json=attendees_json,
        topic=topic,
        duration_minutes=duration_minutes,
        meeting_type=meeting_type,
        slot_snapshot_hash=slot_snapshot_hash,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(row)
    await session.flush()
    return row
