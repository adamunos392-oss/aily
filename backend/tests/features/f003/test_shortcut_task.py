"""AC-F003-07 执行任务入口走同一创建会议链。"""

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.features.f003.conftest import (
    MEETING_QUERY,
    PRODUCT_CHOICE,
    create_owned_conversation,
    post_turn,
)

from src.db.models import Meeting


async def test_shortcut_task_same_confirmation_chain(
    client: TestClient,
    f003_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    conversation_id = create_owned_conversation(client)
    pending = post_turn(
        client,
        conversation_id,
        MEETING_QUERY,
        entry_source="shortcut_task",
        choice_id=PRODUCT_CHOICE,
    )
    assert pending["status"] == "awaiting_confirmation"
    confirmation = pending["assistant_message"]["confirmation"]
    approved = client.post(
        f"/api/conversations/{conversation_id}/confirmations/{confirmation['confirmation_id']}/approve",
        json={"turn_id": pending["turn_id"]},
    )
    assert approved.status_code == 200
    data = approved.json()["data"]
    assert data["status"] == "replied"
    assert data["assistant_message"]["message_type"] == "meeting_success"
    async with f003_session_maker() as session:
        count = int((await session.execute(select(func.count()).select_from(Meeting))).scalar_one())
    assert count == 1
