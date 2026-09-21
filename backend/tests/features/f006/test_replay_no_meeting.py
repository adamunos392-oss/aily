"""AC-F006-03 回放不产生成功会议、不调用 approve。"""

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.features.f006.conftest import assert_envelope_ok

from src.db.models import Confirmation, Meeting


async def _count(session_maker: async_sessionmaker[AsyncSession], model: type[object]) -> int:
    async with session_maker() as session:
        result = await session.execute(select(func.count()).select_from(model))
        return int(result.scalar_one())


async def test_replay_does_not_create_meetings(
    client: TestClient,
    f006_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    before_meetings = await _count(f006_session_maker, Meeting)
    before_confirmations = await _count(f006_session_maker, Confirmation)
    timeout = assert_envelope_ok(client.get("/api/evaluation_cases/eval-meeting-timeout").json())
    stale = assert_envelope_ok(client.get("/api/evaluation_cases/eval-meeting-stale").json())
    timeout_titles = [item["title_zh"] for item in timeout["case"]["trace_events"]]
    assert "会议已创建" not in timeout_titles
    assert not any(item["title_zh"] == "已回复 · 会议已创建" for item in timeout["case"]["trace_events"])
    finals = [item for item in timeout["case"]["trace_events"] if item["node"] == "final"]
    assert finals
    assert all("无会议已创建" in item["title_zh"] for item in finals)
    stale_titles = [item["title_zh"] for item in stale["case"]["trace_events"]]
    assert "会议已创建" not in stale_titles
    after_meetings = await _count(f006_session_maker, Meeting)
    after_confirmations = await _count(f006_session_maker, Confirmation)
    assert after_meetings == before_meetings
    assert after_confirmations == before_confirmations
