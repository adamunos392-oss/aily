"""AC-F004-04 员工修改后以编辑版为准。"""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.features.f004.conftest import (
    WORK_FACT_ARCH,
    assert_envelope_ok,
    create_owned_conversation,
    post_report_turn,
)

from src.db.models import ReportDraft

EDITED = "本周完成：需求评审纪要整理。"


def test_edit_draft_persists_employee_version(client: TestClient) -> None:
    conversation_id = create_owned_conversation(client)
    data = post_report_turn(client, conversation_id)
    turn_id = data["turn_id"]
    draft = data["assistant_message"]["report_draft"]
    draft_id = draft["draft_id"]
    original = draft["content"]
    assert WORK_FACT_ARCH in original
    assert draft["is_edited"] is False

    response = client.patch(
        f"/api/conversations/{conversation_id}/turns/{turn_id}/report_drafts/{draft_id}",
        json={"content": EDITED},
    )
    assert response.status_code == 200, response.text
    saved = assert_envelope_ok(response.json())
    assert saved["draft_id"] == draft_id
    assert saved["turn_id"] == turn_id
    assert saved["content"] == EDITED
    assert saved["is_edited"] is True

    fetched = client.get(f"/api/conversations/{conversation_id}/turns/{turn_id}")
    again = assert_envelope_ok(fetched.json())
    report = again["assistant_message"]["report_draft"]
    assert report["content"] == EDITED
    assert report["is_edited"] is True
    assert original not in report["content"]


async def test_edit_draft_row_is_edited(
    client: TestClient,
    f004_session_maker: async_sessionmaker[AsyncSession],
) -> None:
    conversation_id = create_owned_conversation(client)
    data = post_report_turn(client, conversation_id)
    turn_id = data["turn_id"]
    draft_id = data["assistant_message"]["report_draft"]["draft_id"]
    client.patch(
        f"/api/conversations/{conversation_id}/turns/{turn_id}/report_drafts/{draft_id}",
        json={"content": EDITED},
    )
    async with f004_session_maker() as session:
        row = (
            await session.execute(select(ReportDraft).where(ReportDraft.draft_id == draft_id))
        ).scalar_one()
        assert int(row.is_edited) == 1
        assert row.content == EDITED


def test_empty_content_is_validation_error(client: TestClient) -> None:
    conversation_id = create_owned_conversation(client)
    data = post_report_turn(client, conversation_id)
    turn_id = data["turn_id"]
    draft_id = data["assistant_message"]["report_draft"]["draft_id"]
    response = client.patch(
        f"/api/conversations/{conversation_id}/turns/{turn_id}/report_drafts/{draft_id}",
        json={"content": "   "},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == 400
    assert body["message"] == "content 不能为空"
    assert body["data"] is None


def test_missing_draft_is_not_found(client: TestClient) -> None:
    conversation_id = create_owned_conversation(client)
    data = post_report_turn(client, conversation_id)
    response = client.patch(
        f"/api/conversations/{conversation_id}/turns/{data['turn_id']}/report_drafts/draft-missing",
        json={"content": EDITED},
    )
    assert response.status_code == 404
    body = response.json()
    assert body["message"] == "周报草稿不存在"
