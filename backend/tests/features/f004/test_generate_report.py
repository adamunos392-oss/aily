"""AC-F004-01 生成本周周报且命中技能。"""

from fastapi.testclient import TestClient
from tests.features.f004.conftest import create_owned_conversation, post_report_turn


def test_generate_weekly_report_hits_skill(client: TestClient) -> None:
    conversation_id = create_owned_conversation(client)
    data = post_report_turn(client, conversation_id)
    assert data["status"] == "replied"
    assert data["intent"]["intent"] == "generate_work_report"
    assert data["intent"]["operation_type"] == "READ"
    assert data["route_decision"]["route_type"] == "SKILL"
    assert data["route_decision"]["target"] == "generate_work_report"
    message = data["assistant_message"]
    assert message["message_type"] == "report_draft"
    assert message["text"] == "已命中技能：生成工作周报。按固定步骤生成本周周报，事实来自本轮工作消息。"
    draft = message["report_draft"]
    assert draft["skill_name"] == "生成工作周报"
    assert draft["is_edited"] is False
    summaries = [item["summary"] for item in data["trace_events"]]
    titles = [item["title_zh"] for item in data["trace_events"]]
    assert "技能：生成工作周报" in summaries
    assert "生成工作周报 · 套用简洁中文事项列表" in summaries
    assert "已取本周工作消息" in summaries
    assert "过滤闲聊" in summaries
    assert "抽取工作事项" in summaries
    assert "套用简洁中文事项列表" in summaries
    assert "润色" in summaries
    assert "已回复 · 可编辑周报" in summaries
    assert "路由" in titles
    assert "技能" in titles
    assert "原子能力" in titles
    assert all(item["node"] != "confirmation" for item in data["trace_events"])
    assert all(item["node"] != "risk_permission" for item in data["trace_events"])
