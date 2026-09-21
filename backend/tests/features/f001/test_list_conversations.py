"""AC-F001-03 / API-F001-02 最近对话列表。"""

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.features.f001.conftest import add_conversation, assert_envelope_error, assert_envelope_ok

from src.core.config import settings


async def test_list_conversations_only_current_user(
    client: TestClient,
    f001_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    async with f001_session_maker() as session:
        await add_conversation(
            session,
            conversation_id="conv-other-user",
            user_id="someone-else",
            title="他人对话",
            preview="不该出现",
        )
        await session.commit()

    response = client.get("/api/conversations")
    assert response.status_code == 200
    data = assert_envelope_ok(response.json())
    items = data["items"]
    assert isinstance(items, list)
    ids = {item["conversation_id"] for item in items}
    assert "conv-other-user" not in ids
    assert settings.meeting_timeout_demo_conversation_id in ids
    assert data["total"] == len(items)
    for item in items:
        assert set(item.keys()) == {"conversation_id", "title", "updated_at", "preview"}


def test_list_conversations_limit_out_of_range(client: TestClient) -> None:
    too_small = client.get("/api/conversations", params={"limit": 0})
    assert too_small.status_code == 400
    assert_envelope_error(too_small.json(), 400, "limit 必须在 1 到 100 之间")

    too_large = client.get("/api/conversations", params={"limit": 101})
    assert too_large.status_code == 400
    assert_envelope_error(too_large.json(), 400, "limit 必须在 1 到 100 之间")
