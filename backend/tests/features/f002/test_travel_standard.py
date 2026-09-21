"""AC-F002-01 差旅标准有据作答。"""

from fastapi.testclient import TestClient
from tests.features.f002.conftest import (
    assert_envelope_error,
    assert_envelope_ok,
    create_owned_conversation,
)


def test_travel_standard_replied_with_table(client: TestClient) -> None:
    conversation_id = create_owned_conversation(client)
    response = client.post(
        f"/api/conversations/{conversation_id}/turns",
        json={
            "content": "公司的差旅住宿标准是什么？",
            "entry_source": "manual",
            "choice_id": None,
            "client_turn_key": None,
        },
    )
    assert response.status_code == 200
    data = assert_envelope_ok(response.json())
    assert data["status"] == "replied"
    assert data["user_message"] == "公司的差旅住宿标准是什么？"
    message = data["assistant_message"]
    assert message["message_type"] == "knowledge_table"
    rows = { (row["level"], row["city_type"], row["limit_cny"]) for row in message["table_rows"] }
    assert ("P1-P3", "一线城市", 800) in rows
    assert ("P1-P3", "其他城市", 600) in rows
    assert ("P4 及以上", "一线城市", 1200) in rows
    excerpts = " ".join(item["excerpt"] for item in data["citations"])
    assert "800" in excerpts
    assert data["intent"]["operation_type"] == "READ"
    assert data["route_decision"]["route_type"] == "RAG"

    fetched = client.get(f"/api/conversations/{conversation_id}/turns/{data['turn_id']}")
    assert fetched.status_code == 200
    again = assert_envelope_ok(fetched.json())
    assert again["turn_id"] == data["turn_id"]
    assert again["status"] == "replied"
    assert again["assistant_message"]["table_rows"] == message["table_rows"]


def test_empty_content_rejected(client: TestClient) -> None:
    conversation_id = create_owned_conversation(client)
    response = client.post(
        f"/api/conversations/{conversation_id}/turns",
        json={"content": "   ", "entry_source": "manual"},
    )
    assert response.status_code == 400
    assert_envelope_error(response.json(), 400, "content 不能为空")
