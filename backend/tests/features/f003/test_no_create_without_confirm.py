"""AC-F003-04 未确认不得创建；取消不写 meetings。"""

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.features.f003.conftest import create_owned_conversation, reach_pending_confirmation

from src.db.models import Meeting


async def test_pending_confirmation_does_not_create_meeting(
    client: TestClient,
    f003_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    conversation_id = create_owned_conversation(client)
    pending = reach_pending_confirmation(client, conversation_id)
    assert "会议已创建" not in (pending["assistant_message"]["text"] or "")
    async with f003_session_maker() as session:
        count = int((await session.execute(select(func.count()).select_from(Meeting))).scalar_one())
    assert count == 0

    confirmation = pending["assistant_message"]["confirmation"]
    cancelled = client.post(
        f"/api/conversations/{conversation_id}/confirmations/{confirmation['confirmation_id']}/cancel",
        json={"turn_id": pending["turn_id"], "reason": None},
    )
    assert cancelled.status_code == 200
    data = cancelled.json()["data"]
    assert data["assistant_message"]["message_type"] == "text"
    assert data["assistant_message"]["confirmation"]["status"] == "cancelled"
    async with f003_session_maker() as session:
        count = int((await session.execute(select(func.count()).select_from(Meeting))).scalar_one())
    assert count == 0

    again = client.post(
        f"/api/conversations/{conversation_id}/confirmations/{confirmation['confirmation_id']}/approve",
        json={"turn_id": pending["turn_id"]},
    )
    assert again.status_code == 409
