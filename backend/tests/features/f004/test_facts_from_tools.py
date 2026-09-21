"""AC-F004-02 事实来自本轮工作消息且不含闲聊。"""

import pytest
from fastapi.testclient import TestClient
from tests.features.f004.conftest import (
    CHITCHAT,
    WORK_FACT_ARCH,
    WORK_FACT_REVIEW,
    create_owned_conversation,
    post_report_turn,
)

from src.models.agent.types import ToolCall, ToolResult
from src.repositories.mock.tool_adapter import ToolAdapter


def test_report_facts_come_from_seed_work_messages(client: TestClient) -> None:
    conversation_id = create_owned_conversation(client)
    data = post_report_turn(client, conversation_id)
    content = data["assistant_message"]["report_draft"]["content"]
    assert WORK_FACT_ARCH in content
    assert WORK_FACT_REVIEW in content
    assert CHITCHAT not in content
    assert "绩效" not in content
    assert "薪资" not in content


def test_report_facts_follow_this_round_tool_payload(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    extra_work = "完成本周预算对齐"
    extra_chat = "周末去爬山吗"

    def fake_work_messages(self: ToolAdapter, call: ToolCall) -> ToolResult:
        return ToolResult(
            call_id=call.call_id,
            tool_id=call.tool_id,
            status="success",
            payload={
                "messages": [
                    {"message_id": "msg-work-budget", "kind": "work", "content": extra_work},
                    {"message_id": "msg-chat-hike", "kind": "chitchat", "content": extra_chat},
                ]
            },
            error_message=None,
        )

    monkeypatch.setattr(ToolAdapter, "_work_messages", fake_work_messages)
    conversation_id = create_owned_conversation(client)
    data = post_report_turn(client, conversation_id)
    content = data["assistant_message"]["report_draft"]["content"]
    assert extra_work in content
    assert extra_chat not in content
    assert WORK_FACT_ARCH not in content
    assert WORK_FACT_REVIEW not in content
