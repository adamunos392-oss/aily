"""AC-F005-02 只读查询不创建会议、不写确认单。"""

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.features.f005.conftest import create_owned_conversation, post_room_query

from src.db.models import Confirmation, Meeting


async def test_room_query_is_read_only(
    client: TestClient,
    f005_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    conversation_id = create_owned_conversation(client)
    async with f005_session_maker() as session:
        meetings_before = int(
            (await session.execute(select(func.count()).select_from(Meeting))).scalar_one()
        )
        confirmations_before = int(
            (await session.execute(select(func.count()).select_from(Confirmation))).scalar_one()
        )

    data = post_room_query(client, conversation_id)
    nodes = [item["node"] for item in data["trace_events"]]
    assert "confirmation" not in nodes
    assert "risk_permission" not in nodes
    assert "tool_call" in nodes
    assert data["assistant_message"]["confirmation"] is None
    text = str(data["assistant_message"])
    assert "会议已创建" not in text
    assert data["intent"]["operation_type"] == "READ"
    assert data["route_decision"]["display_route"] == "只读查询"

    async with f005_session_maker() as session:
        meetings_after = int(
            (await session.execute(select(func.count()).select_from(Meeting))).scalar_one()
        )
        confirmations_after = int(
            (await session.execute(select(func.count()).select_from(Confirmation))).scalar_one()
        )
    assert meetings_after == meetings_before
    assert confirmations_after == confirmations_before
