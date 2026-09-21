"""AC-F002-02 无可靠依据时拒答。"""

from fastapi.testclient import TestClient
from tests.features.f002.conftest import assert_envelope_ok, create_owned_conversation

from src.core.config import settings


def test_refuse_query_has_no_fake_citations(client: TestClient) -> None:
    conversation_id = create_owned_conversation(client)
    response = client.post(
        f"/api/conversations/{conversation_id}/turns",
        json={
            "content": settings.knowledge_refuse_demo_query,
            "entry_source": "manual",
        },
    )
    assert response.status_code == 200
    data = assert_envelope_ok(response.json())
    assert data["status"] == "refused"
    assert data["assistant_message"]["message_type"] == "refusal"
    assert data["citations"] == []
    text = data["assistant_message"]["text"]
    assert "未找到可靠企业知识依据" not in str(data["citations"])
    assert "上市时间表" not in str(text)
    assert data["assistant_message"]["table_rows"] is None
