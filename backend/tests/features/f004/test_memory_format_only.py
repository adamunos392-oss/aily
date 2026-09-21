"""AC-F004-03 偏好只影响格式，记忆不含工作事实。"""

from fastapi.testclient import TestClient
from tests.features.f004.conftest import (
    WORK_FACT_ARCH,
    WORK_FACT_REVIEW,
    create_owned_conversation,
    post_report_turn,
)


def test_memory_only_controls_format(client: TestClient) -> None:
    conversation_id = create_owned_conversation(client)
    data = post_report_turn(client, conversation_id)
    content = data["assistant_message"]["report_draft"]["content"]
    assert content.startswith("本周工作周报（林小北）")
    assert "1. " in content
    assert "2. " in content
    assert WORK_FACT_ARCH in content
    assert WORK_FACT_REVIEW in content
    memory_events = [item for item in data["trace_events"] if item["node"] == "memory"]
    assert memory_events
    payload = memory_events[0]["payload"]
    assert set(payload.keys()) == {"template_style", "language", "length"}
    assert payload["template_style"] == "bullet_list"
    assert payload["language"] == "zh-CN"
    assert payload["length"] == "concise"
    dumped = str(payload)
    assert WORK_FACT_ARCH not in dumped
    assert WORK_FACT_REVIEW not in dumped
    assert "张明" not in dumped
    assert data["assistant_message"]["report_draft"]["skill_name"] == "生成工作周报"
