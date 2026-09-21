"""快捷入口 shortcut_report 与自然语言同一周报链。"""

from fastapi.testclient import TestClient
from tests.features.f004.conftest import (
    WORK_FACT_ARCH,
    create_owned_conversation,
    post_report_turn,
)


def test_shortcut_report_same_chain(client: TestClient) -> None:
    conversation_id = create_owned_conversation(client)
    data = post_report_turn(
        client,
        conversation_id,
        content="帮我生成本周周报",
        entry_source="shortcut_report",
    )
    assert data["intent"]["intent"] == "generate_work_report"
    assert data["assistant_message"]["message_type"] == "report_draft"
    assert data["assistant_message"]["report_draft"]["skill_name"] == "生成工作周报"
    assert WORK_FACT_ARCH in data["assistant_message"]["report_draft"]["content"]
    assert data["assistant_message"]["confirmation"] is None
