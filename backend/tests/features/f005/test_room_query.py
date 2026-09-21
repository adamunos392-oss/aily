"""AC-F005-01 查询明天下午 3 点后可用会议室。"""

from fastapi.testclient import TestClient
from tests.features.f005.conftest import create_owned_conversation, post_room_query


def test_room_query_returns_seeded_rooms(client: TestClient) -> None:
    conversation_id = create_owned_conversation(client)
    data = post_room_query(client, conversation_id)
    assert data["status"] == "replied"
    assert data["assistant_message"]["message_type"] == "room_list"
    assert data["assistant_message"]["text"] == "明天下午 15:00 以后可用的会议室："
    rooms = data["assistant_message"]["rooms"]
    names = {item["room_name"] for item in rooms}
    assert names == {"星河 3 号", "启航厅"}
    assert data["route_decision"]["route_type"] == "READ_TOOL"
    assert data["intent"]["intent"] == "query_meeting_rooms"
    assert data["intent"]["operation_type"] == "READ"
    titles = {item["node"]: item["title_zh"] for item in data["trace_events"]}
    summaries = {item["node"]: item["summary"] for item in data["trace_events"]}
    assert titles["router"] == "路由"
    assert titles["tool_call"] == "原子能力"
    assert summaries["intent"] == "意图：查询会议室　只读"
    assert summaries["tool_call"] == "查询会议室成功"
    assert summaries["final"] == "已回复 · 未创建会议"

    fetched = client.get(f"/api/conversations/{conversation_id}/turns/{data['turn_id']}")
    assert fetched.status_code == 200
    again = fetched.json()["data"]
    assert again["assistant_message"]["rooms"] == rooms


def test_shortcut_query_entry_source(client: TestClient) -> None:
    conversation_id = create_owned_conversation(client)
    data = post_room_query(client, conversation_id, entry_source="shortcut_query")
    assert data["status"] == "replied"
    assert data["assistant_message"]["message_type"] == "room_list"
    assert {item["room_name"] for item in data["assistant_message"]["rooms"]} == {
        "星河 3 号",
        "启航厅",
    }
