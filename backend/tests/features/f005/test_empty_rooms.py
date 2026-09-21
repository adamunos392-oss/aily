"""AC-F005-03 无可用会议室时不编造预订成功。"""

import pytest
from fastapi.testclient import TestClient
from tests.features.f005.conftest import create_owned_conversation, post_room_query

from src.repositories.mock.tool_adapter import ToolAdapter


def test_empty_rooms_does_not_claim_booking(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ToolAdapter, "demo_rooms", lambda self: [])
    conversation_id = create_owned_conversation(client)
    data = post_room_query(client, conversation_id)
    assert data["status"] == "replied"
    assert data["assistant_message"]["message_type"] == "room_list"
    assert data["assistant_message"]["rooms"] == []
    assert data["assistant_message"]["text"] == "该时段没有可用会议室。"
    assert "会议已创建" not in data["assistant_message"]["text"]
    assert "已预订" not in data["assistant_message"]["text"]
    assert "confirmation" not in [item["node"] for item in data["trace_events"]]
    summaries = {item["node"]: item["summary"] for item in data["trace_events"]}
    assert summaries["tool_call"] == "查询会议室 · 无空闲"
    assert summaries["final"] == "已回复 · 未预订、未创建会议"
