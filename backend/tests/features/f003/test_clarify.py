"""AC-F003-02 缺必要信息时澄清且不创建。"""

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.features.f003.conftest import CLARIFY_QUERY, create_owned_conversation, post_turn

from src.db.models import Confirmation, Meeting


async def test_missing_time_clarifies_without_creating(
    client: TestClient,
    f003_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    conversation_id = create_owned_conversation(client)
    data = post_turn(client, conversation_id, CLARIFY_QUERY)
    assert data["status"] == "clarifying"
    assert data["assistant_message"]["message_type"] == "clarification"
    assert data["assistant_message"]["text"] == "还需要补全会议时间。请问安排在哪一天、几点？"
    assert "会议已创建" not in (data["assistant_message"]["text"] or "")
    assert data["assistant_message"]["confirmation"] is None

    async with f003_session_maker() as session:
        meetings = int((await session.execute(select(func.count()).select_from(Meeting))).scalar_one())
        confirmations = int(
            (await session.execute(select(func.count()).select_from(Confirmation))).scalar_one()
        )
    assert meetings == 0
    assert confirmations == 0
