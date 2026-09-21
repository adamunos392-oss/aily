"""AC-F001-01 / API-F001-03 新建空上下文对话。"""

from fastapi.testclient import TestClient
from tests.features.f001.conftest import assert_envelope_error, assert_envelope_ok

from src.core.config import settings


def test_create_conversation_empty_context(client: TestClient) -> None:
    response = client.post("/api/conversations", json={"title": None})
    assert response.status_code == 200
    data = assert_envelope_ok(response.json())
    assert data["title"] == settings.conversation_default_title
    assert data["turns"] == []
    assert data["active_slot_state"] is None
    assert data["active_confirmation"] is None
    assert data["conversation_id"].startswith("conv-")

    listed = client.get("/api/conversations")
    list_data = assert_envelope_ok(listed.json())
    ids = {item["conversation_id"] for item in list_data["items"]}
    assert data["conversation_id"] in ids

    detail = client.get(f"/api/conversations/{data['conversation_id']}")
    detail_data = assert_envelope_ok(detail.json())
    assert detail_data["turns"] == []
    assert detail_data["active_slot_state"] is None
    assert detail_data["active_confirmation"] is None


def test_create_conversation_rejects_non_string_title(client: TestClient) -> None:
    response = client.post("/api/conversations", json={"title": 123})
    assert response.status_code == 400
    assert_envelope_error(response.json(), 400, "title 必须是字符串或 null")
