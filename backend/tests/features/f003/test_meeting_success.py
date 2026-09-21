"""AC-F003-01 消歧后确认并核验成功。"""

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


async def test_meeting_created_after_disambiguation_and_approve(
    client: TestClient,
    f003_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    conversation_id = create_owned_conversation(client)
    first = post_turn(client, conversation_id, MEETING_QUERY)
    assert first["status"] == "clarifying"
    assert first["assistant_message"]["message_type"] == "disambiguation"
    labels = {item["label"] for item in first["assistant_message"]["choices"]}
    assert labels == {"张明 · 产品部", "张明 · 财务部"}
    assert "会议已创建" not in (first["assistant_message"]["text"] or "")

    pending = post_turn(client, conversation_id, MEETING_QUERY, choice_id=PRODUCT_CHOICE)
    assert pending["status"] == "awaiting_confirmation"
    confirmation = pending["assistant_message"]["confirmation"]
    assert confirmation["status"] == "pending"
    assert confirmation["meeting_time"] == "明天下午 15:00"
    assert "张明（产品部）" in confirmation["attendees"]
    assert "林小北" in confirmation["attendees"]
    nodes = [item["node"] for item in pending["trace_events"]]
    assert "risk_permission" in nodes
    assert "confirmation" in nodes
    assert pending["assistant_message"]["message_type"] != "meeting_success"

    approved = client.post(
        f"/api/conversations/{conversation_id}/confirmations/{confirmation['confirmation_id']}/approve",
        json={"turn_id": pending["turn_id"]},
    )
    assert approved.status_code == 200
    data = approved.json()["data"]
    assert data["status"] == "replied"
    assert data["assistant_message"]["message_type"] == "meeting_success"
    assert data["assistant_message"]["text"] == "会议已创建。"
    assert data["assistant_message"]["confirmation"]["status"] == "approved"
    tool_ids = [
        item["payload"]["tool_id"]
        for item in data["trace_events"]
        if item["node"] == "tool_call"
    ]
    assert tool_ids == ["people_lookup", "calendar_check", "meeting_create"]
    assert all(
        item["payload"]["status"] == "success"
        for item in data["trace_events"]
        if item["node"] == "tool_call"
    )
    nodes_after = [item["node"] for item in data["trace_events"]]
    assert "risk_permission" in nodes_after
    assert "confirmation" in nodes_after
    assert "result_validate" in nodes_after

    async with f003_session_maker() as session:
        count = int((await session.execute(select(func.count()).select_from(Meeting))).scalar_one())
    assert count == 1
