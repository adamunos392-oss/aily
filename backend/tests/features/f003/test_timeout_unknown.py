"""AC-F003-06 超时演示对话确认后为未知且不写 meetings。"""

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.features.f003.conftest import reach_pending_confirmation

from src.core.config import settings
from src.db.models import Meeting


async def test_timeout_demo_conversation_stays_unknown(
    client: TestClient,
    f003_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    conversation_id = settings.meeting_timeout_demo_conversation_id
    pending = reach_pending_confirmation(client, conversation_id)
    confirmation = pending["assistant_message"]["confirmation"]
    approved = client.post(
        f"/api/conversations/{conversation_id}/confirmations/{confirmation['confirmation_id']}/approve",
        json={"turn_id": pending["turn_id"]},
    )
    assert approved.status_code == 200
    data = approved.json()["data"]
    assert data["status"] == "unknown"
    assert data["assistant_message"]["message_type"] == "meeting_unknown"
    assert data["assistant_message"]["text"] == "已确认的会议信息仍保留，但系统未在约定等待内得到确定成功。"
    finals = [item["summary"] for item in data["trace_events"] if item["node"] == "final"]
    assert finals
    assert all("会议已创建" not in item for item in finals)
    async with f003_session_maker() as session:
        count = int((await session.execute(select(func.count()).select_from(Meeting))).scalar_one())
    assert count == 0
