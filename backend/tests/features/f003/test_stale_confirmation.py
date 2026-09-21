"""AC-F003-05 改关键时间后旧确认作废。"""

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.features.f003.conftest import (
    MEETING_QUERY_TWO,
    create_owned_conversation,
    reach_pending_confirmation,
)

from src.db.models import Meeting


async def test_changing_time_invalidates_old_confirmation(
    client: TestClient,
    f003_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    conversation_id = create_owned_conversation(client)
    pending = reach_pending_confirmation(client, conversation_id, MEETING_QUERY_TWO)
    old = pending["assistant_message"]["confirmation"]
    assert old["meeting_time"] == "明天下午 14:00"

    patched = client.patch(
        f"/api/conversations/{conversation_id}/turns/{pending['turn_id']}/slots",
        json={"updates": {"meeting_time": "明天下午三点"}},
    )
    assert patched.status_code == 200
    data = patched.json()["data"]
    assert data["status"] == "awaiting_confirmation"
    new = data["assistant_message"]["confirmation"]
    assert new["confirmation_id"] != old["confirmation_id"]
    assert new["status"] == "pending"
    assert new["meeting_time"] == "明天下午 15:00"
    statuses = [
        (item["payload"].get("status"), item["payload"].get("meeting_time"))
        for item in data["trace_events"]
        if item["node"] == "confirmation"
    ]
    assert ("invalidated", "14:00") in statuses
    assert ("pending", None) in statuses or any(item[0] == "pending" for item in statuses)

    stale = client.post(
        f"/api/conversations/{conversation_id}/confirmations/{old['confirmation_id']}/approve",
        json={"turn_id": pending["turn_id"]},
    )
    assert stale.status_code == 409
    async with f003_session_maker() as session:
        count = int((await session.execute(select(func.count()).select_from(Meeting))).scalar_one())
    assert count == 0
