"""AC-F002-03 只读知识问答事件流不含确认节点。"""

from fastapi.testclient import TestClient
from tests.features.f002.conftest import assert_envelope_ok, create_owned_conversation


def test_travel_trace_is_read_only(client: TestClient) -> None:
    conversation_id = create_owned_conversation(client)
    response = client.post(
        f"/api/conversations/{conversation_id}/turns",
        json={"content": "公司的差旅住宿标准是什么？", "entry_source": "manual"},
    )
    data = assert_envelope_ok(response.json())
    nodes = [item["node"] for item in data["trace_events"]]
    assert "query_rewrite" in nodes
    assert "intent" in nodes
    assert "router" in nodes
    assert "rag_retrieve" in nodes
    assert "citation_validate" in nodes
    assert "final" in nodes
    assert "confirmation" not in nodes
    assert "risk_permission" not in nodes
    sequences = [item["sequence"] for item in data["trace_events"]]
    assert sequences == sorted(sequences)
    assert data["intent"]["operation_type"] == "READ"
