"""AC-F002-04 引用与来源一致。"""

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.features.f002.conftest import (
    assert_envelope_error,
    assert_envelope_ok,
    create_owned_conversation,
)

from src.core.config import settings
from src.db.models import Conversation, utc_now_iso


def test_citations_match_table_numbers(client: TestClient) -> None:
    conversation_id = create_owned_conversation(client)
    response = client.post(
        f"/api/conversations/{conversation_id}/turns",
        json={"content": "公司的差旅住宿标准是什么？", "entry_source": "manual"},
    )
    data = assert_envelope_ok(response.json())
    citations = data["citations"]
    assert citations
    titles = {item["document_title"] for item in citations}
    sections = {item["section"] for item in citations}
    excerpts = " ".join(item["excerpt"] for item in citations)
    assert any("差旅管理制度" in title for title in titles)
    assert any("3.2" in section for section in sections)
    assert "800" in excerpts
    ids = {item["knowledge_entry_id"] for item in citations}
    assert "know-travel-p1-tier1" in ids

    fetched = client.get(f"/api/conversations/{conversation_id}/turns/{data['turn_id']}")
    again = assert_envelope_ok(fetched.json())
    assert again["citations"] == citations


def test_missing_turn_not_found(client: TestClient) -> None:
    conversation_id = create_owned_conversation(client)
    response = client.get(f"/api/conversations/{conversation_id}/turns/turn-missing")
    assert response.status_code == 404
    assert_envelope_error(response.json(), 404, "轮次不存在")


def test_missing_conversation_not_found(client: TestClient) -> None:
    missing = client.post(
        "/api/conversations/conv-does-not-exist/turns",
        json={"content": "公司的差旅住宿标准是什么？"},
    )
    assert missing.status_code == 404
    assert_envelope_error(missing.json(), 404, "对话不存在")


async def test_foreign_conversation_conflict(
    client: TestClient,
    f002_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    now = utc_now_iso()
    async with f002_session_maker() as session:
        session.add(
            Conversation(
                conversation_id="conv-foreign-f002",
                user_id="someone-else",
                title="他人对话",
                preview=None,
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()

    response = client.post(
        "/api/conversations/conv-foreign-f002/turns",
        json={"content": "公司的差旅住宿标准是什么？"},
    )
    assert response.status_code == 409
    assert_envelope_error(response.json(), 409, "对话不属于当前身份")
    assert settings.mock_user_id != "someone-else"
