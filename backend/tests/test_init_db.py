"""SQLite 建表与种子数据测试。使用临时库，禁止 drop 运行时业务库。"""

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from sqlalchemy import func, inspect, select, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.core.config import settings
from src.db.models import (
    Conversation,
    EvaluationCase,
    KnowledgeEntry,
    Meeting,
    MeetingRoom,
    Person,
    WorkMessage,
)
from src.db.seed import seed_database
from src.db.session import (
    DATABASE_FILE,
    create_all_tables,
    create_engine,
    sqlite_url_for,
)

BUSINESS_TABLES = {
    "conversations",
    "turns",
    "citations",
    "confirmations",
    "trace_events",
    "report_drafts",
    "knowledge_entries",
    "work_messages",
    "people",
    "meeting_rooms",
    "meetings",
    "evaluation_cases",
}

EVALUATION_CASE_IDS = {
    "eval-qa-travel",
    "eval-qa-refuse",
    "eval-meeting-success",
    "eval-meeting-timeout",
    "eval-meeting-stale",
    "eval-report",
    "eval-rooms",
}

BACKEND_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
async def isolated_engine(tmp_path: Path) -> AsyncGenerator[AsyncEngine, None]:
    db_file = tmp_path / "aily-test.db"
    assert db_file.resolve() != DATABASE_FILE.resolve()
    engine = create_engine(sqlite_url_for(db_file))
    await create_all_tables(engine)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def isolated_session(isolated_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(
        isolated_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with maker() as session:
        await seed_database(session)
        await session.commit()
        yield session


def _sync_table_names(sync_conn: Connection) -> set[str]:
    return set(inspect(sync_conn).get_table_names())


async def _table_names(engine: AsyncEngine) -> set[str]:
    async with engine.connect() as conn:
        names = await conn.run_sync(_sync_table_names)
    return names


async def test_create_all_creates_business_tables(isolated_engine: AsyncEngine) -> None:
    names = await _table_names(isolated_engine)
    assert BUSINESS_TABLES.issubset(names)


async def test_seed_knowledge_travel_standards(isolated_session: AsyncSession) -> None:
    rows = (await isolated_session.execute(select(KnowledgeEntry))).scalars().all()
    assert rows
    excerpts = " ".join(item.excerpt for item in rows)
    assert "800" in excerpts
    assert "600" in excerpts
    assert "1200" in excerpts
    assert any("职级" in item.excerpt and "城市" in item.excerpt for item in rows)
    refuse_query = settings.knowledge_refuse_demo_query
    haystack = " ".join(
        f"{item.document_title} {item.section} {item.excerpt}" for item in rows if item.is_active == 1
    )
    assert refuse_query not in haystack


async def test_seed_two_zhangming_people(isolated_session: AsyncSession) -> None:
    name = settings.meeting_disambiguation_person_name
    rows = (
        await isolated_session.execute(select(Person).where(Person.display_name == name))
    ).scalars().all()
    departments = {item.department for item in rows}
    assert len(rows) >= 2
    assert settings.mock_user_department in departments
    assert "财务部" in departments


async def test_seed_meeting_rooms(isolated_session: AsyncSession) -> None:
    rows = (await isolated_session.execute(select(MeetingRoom))).scalars().all()
    names = {item.room_name for item in rows}
    assert "星河 3 号" in names
    assert "启航厅" in names
    for room in rows:
        assert room.available_to > room.available_from
        assert room.tomorrow_after_hour == settings.meeting_room_query_after_hour


async def test_seed_work_messages_include_work_and_chitchat(isolated_session: AsyncSession) -> None:
    rows = (await isolated_session.execute(select(WorkMessage))).scalars().all()
    kinds = {item.kind for item in rows}
    assert "work" in kinds
    assert "chitchat" in kinds
    assert any("晚上吃啥" in item.content for item in rows)
    assert all(item.user_id == settings.mock_user_id for item in rows)
    assert all(item.is_this_week == 1 for item in rows)


async def test_seed_evaluation_cases_match_expected_count(isolated_session: AsyncSession) -> None:
    rows = (await isolated_session.execute(select(EvaluationCase))).scalars().all()
    case_ids = {item.case_id for item in rows}
    assert len(rows) == settings.evaluation_case_count_expected
    assert case_ids == EVALUATION_CASE_IDS


async def test_seed_timeout_demo_conversation(isolated_session: AsyncSession) -> None:
    conversation_id = settings.meeting_timeout_demo_conversation_id
    row = (
        await isolated_session.execute(
            select(Conversation).where(Conversation.conversation_id == conversation_id)
        )
    ).scalar_one()
    assert row.user_id == settings.mock_user_id
    meeting_count = (
        await isolated_session.execute(
            select(func.count()).select_from(Meeting).where(Meeting.conversation_id == conversation_id)
        )
    ).scalar_one()
    assert meeting_count == 0


async def test_seed_is_idempotent(isolated_engine: AsyncEngine) -> None:
    maker = async_sessionmaker(
        isolated_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with maker() as session:
        await seed_database(session)
        await session.commit()
        first_people = (await session.execute(select(func.count()).select_from(Person))).scalar_one()
        first_cases = (
            await session.execute(select(func.count()).select_from(EvaluationCase))
        ).scalar_one()
        await seed_database(session)
        await session.commit()
        second_people = (await session.execute(select(func.count()).select_from(Person))).scalar_one()
        second_cases = (
            await session.execute(select(func.count()).select_from(EvaluationCase))
        ).scalar_one()
        timeout_count = (
            await session.execute(
                select(func.count())
                .select_from(Conversation)
                .where(Conversation.conversation_id == settings.meeting_timeout_demo_conversation_id)
            )
        ).scalar_one()
    assert first_people == second_people
    assert first_cases == second_cases == settings.evaluation_case_count_expected
    assert timeout_count == 1


def test_runtime_session_and_seed_do_not_drop_all() -> None:
    session_src = (BACKEND_ROOT / "src" / "db" / "session.py").read_text(encoding="utf-8")
    seed_src = (BACKEND_ROOT / "src" / "db" / "seed.py").read_text(encoding="utf-8")
    script_src = (BACKEND_ROOT / "scripts" / "init_db.py").read_text(encoding="utf-8")
    assert "metadata.drop_all" not in session_src
    assert "metadata.drop_all" not in seed_src
    assert "metadata.drop_all" not in script_src


async def test_isolated_db_is_not_runtime_file(isolated_engine: AsyncEngine) -> None:
    async with isolated_engine.connect() as conn:
        result = await conn.execute(text("PRAGMA database_list"))
        rows = result.all()
    file_paths = [str(item[2]) for item in rows if item[2]]
    assert all(Path(item).resolve() != DATABASE_FILE.resolve() for item in file_paths)
