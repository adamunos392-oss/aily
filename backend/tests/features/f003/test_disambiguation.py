"""AC-F003-03 同名人员必须消歧。"""

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.features.f003.conftest import MEETING_QUERY, create_owned_conversation, post_turn

from src.db.models import Meeting


async def test_two_zhangming_must_be_chosen(
    client: TestClient,
    f003_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    conversation_id = create_owned_conversation(client)
    data = post_turn(client, conversation_id, MEETING_QUERY)
    assert data["status"] == "clarifying"
    assert data["assistant_message"]["message_type"] == "disambiguation"
    assert data["assistant_message"]["text"] == "通讯录里有两位张明，请选择具体的人："
    assert len(data["assistant_message"]["choices"]) >= 2
    async with f003_session_maker() as session:
        meetings = int((await session.execute(select(func.count()).select_from(Meeting))).scalar_one())
    assert meetings == 0
