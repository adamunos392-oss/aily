"""保存周报员工编辑版。API-F004-01。"""

from __future__ import annotations

import json

from pycore.core import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import utc_now_iso
from src.models.report import ReportDraftResponse
from src.models.user_context import UserContext
from src.repositories.conversation import ConversationRepository
from src.repositories.turn import TurnRepository
from src.services.conversation import ConversationNotFoundError
from src.services.turn import ConversationForbiddenError, TurnNotFoundError, _dump_json

logger = get_logger()


class ReportDraftNotFoundError(FileNotFoundError):
    """周报草稿不存在。"""


class EmptyReportContentError(ValueError):
    """content 为空。"""


class ReportService:
    def __init__(
        self,
        db: AsyncSession,
        conversation_repo: ConversationRepository | None = None,
        turn_repo: TurnRepository | None = None,
    ) -> None:
        self.db = db
        self.conversations = (
            conversation_repo if conversation_repo is not None else ConversationRepository(db)
        )
        self.turns = turn_repo if turn_repo is not None else TurnRepository(db)

    async def update_draft(
        self,
        user: UserContext,
        conversation_id: str,
        turn_id: str,
        draft_id: str,
        content: str,
    ) -> ReportDraftResponse:
        text = content.strip()
        if not text:
            raise EmptyReportContentError("content 不能为空")
        conversation = await self.conversations.get_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError("对话不存在")
        if conversation.user_id != user.user_id:
            raise ConversationForbiddenError("对话不属于当前身份")
        turn = await self.turns.get_by_id(conversation_id, turn_id)
        if turn is None:
            raise TurnNotFoundError("轮次不存在")
        draft = await self.turns.get_report_draft(turn_id, draft_id)
        if draft is None:
            raise ReportDraftNotFoundError("周报草稿不存在")
        now = utc_now_iso()
        draft.content = content
        draft.is_edited = 1
        draft.updated_at = now
        payload = json.loads(turn.assistant_payload_json) if turn.assistant_payload_json else {}
        report = payload.get("report_draft")
        if isinstance(report, dict):
            report["content"] = content
            report["is_edited"] = True
            payload["report_draft"] = report
            turn.assistant_payload_json = _dump_json(payload)
        turn.updated_at = now
        await self.db.flush()
        logger.info("周报草稿已保存员工编辑版", turn_id=turn_id, draft_id=draft_id)
        return ReportDraftResponse(
            draft_id=draft.draft_id,
            turn_id=turn_id,
            content=draft.content,
            is_edited=True,
            updated_at=draft.updated_at,
        )
