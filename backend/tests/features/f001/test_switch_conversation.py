"""AC-F001-02 / API-F001-04 切换对话不串槽位与确认单。"""

import json

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.features.f001.conftest import (
    add_conversation,
    add_pending_confirmation,
    add_turn,
    assert_envelope_error,
    assert_envelope_ok,
)

from src.core.config import settings


async def test_switch_conversation_isolates_slot_and_confirmation(
    client: TestClient,
    f001_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    slot_a = {
        "slots": {"meeting_time": "明天下午三点", "attendees": ["张明"], "topic": "项目复盘"},
        "missing_required": [],
        "is_complete": True,
    }
    slot_b = {
        "slots": {"meeting_time": "周五上午十点"},
        "missing_required": ["attendees"],
        "is_complete": False,
    }
    async with f001_session_maker() as session:
        await add_conversation(
            session,
            conversation_id="conv-switch-a",
            user_id=settings.mock_user_id,
            title="对话 A",
            preview="帮我明天下午三点跟张明开会",
            updated_at="2026-09-21T07:00:00Z",
        )
        await add_conversation(
            session,
            conversation_id="conv-switch-b",
            user_id=settings.mock_user_id,
            title="对话 B",
            preview="差旅住宿标准",
            updated_at="2026-09-21T07:10:00Z",
        )
        await add_turn(
            session,
            turn_id="turn-switch-a",
            conversation_id="conv-switch-a",
            content="帮我明天下午三点跟张明开项目复盘会",
            slot_state_json=json.dumps(slot_a, ensure_ascii=False),
        )
        await add_turn(
            session,
            turn_id="turn-switch-b",
            conversation_id="conv-switch-b",
            content="公司的差旅住宿标准是什么？",
            status="replied",
            slot_state_json=json.dumps(slot_b, ensure_ascii=False),
        )
        await add_pending_confirmation(
            session,
            confirmation_id="cfm-switch-a",
            conversation_id="conv-switch-a",
            turn_id="turn-switch-a",
            topic="项目复盘",
            duration_minutes=settings.meeting_default_duration_minutes,
            meeting_type=settings.meeting_default_type,
            slot_snapshot_hash="hash-a",
        )
        await session.commit()

    response_a = client.get("/api/conversations/conv-switch-a")
    assert response_a.status_code == 200
    data_a = assert_envelope_ok(response_a.json())
    assert data_a["active_slot_state"]["slots"]["meeting_time"] == "明天下午三点"
    assert data_a["active_confirmation"]["confirmation_id"] == "cfm-switch-a"
    assert data_a["active_confirmation"]["topic"] == "项目复盘"

    response_b = client.get("/api/conversations/conv-switch-b")
    assert response_b.status_code == 200
    data_b = assert_envelope_ok(response_b.json())
    assert data_b["active_slot_state"]["slots"]["meeting_time"] == "周五上午十点"
    assert data_b["active_confirmation"] is None
    assert data_b["conversation_id"] == "conv-switch-b"
    turn_ids = {item["turn_id"] for item in data_b["turns"]}
    assert "turn-switch-a" not in turn_ids
    assert "turn-switch-b" in turn_ids


def test_get_conversation_not_found(client: TestClient) -> None:
    response = client.get("/api/conversations/conv-does-not-exist")
    assert response.status_code == 404
    assert_envelope_error(response.json(), 404, "对话不存在")


async def test_get_other_user_conversation_not_found(
    client: TestClient,
    f001_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    async with f001_session_maker() as session:
        await add_conversation(
            session,
            conversation_id="conv-foreign",
            user_id="someone-else",
            title="他人对话",
        )
        await session.commit()

    response = client.get("/api/conversations/conv-foreign")
    assert response.status_code == 404
    assert_envelope_error(response.json(), 404, "对话不存在")
