"""对话业务：按当前身份隔离列表/详情，新建空上下文。"""

from __future__ import annotations

import json
import uuid
from typing import Any, cast

from pycore.core import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import AppSettings, settings
from src.db.models import Confirmation, Conversation, Turn, utc_now_iso
from src.models.agent.types import (
    ConfirmationStatus,
    ConfirmationSummary,
    MeetingType,
    SlotState,
    TurnStatus,
)
from src.models.conversation import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationSummary,
    TurnSummary,
)
from src.models.user_context import UserContext
from src.repositories.conversation import ConversationRepository

logger = get_logger()


class ConversationNotFoundError(FileNotFoundError):
    """对话不存在或不属于当前身份。"""


def _new_conversation_id() -> str:
    return f"conv-{uuid.uuid4().hex[:12]}"


def _parse_json_object(raw: str | None) -> dict[str, Any] | None:
    if raw is None or not raw.strip():
        return None
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("JSON 字段无法解析", detail="invalid json")
        return None
    if not isinstance(loaded, dict):
        logger.warning("JSON 字段不是对象", detail="expected object")
        return None
    return loaded


def _assistant_summary_content(turn: Turn) -> str:
    if turn.role == "assistant":
        return turn.content
    payload = _parse_json_object(turn.assistant_payload_json)
    if payload is None:
        return ""
    text = payload.get("text")
    return text if isinstance(text, str) else ""


def _to_turn_summaries(turn: Turn) -> list[TurnSummary]:
    user_content = turn.content if turn.role == "user" else ""
    user = TurnSummary(
        turn_id=turn.turn_id,
        role="user",
        content=user_content,
        status=cast(TurnStatus, turn.status),
        created_at=turn.created_at,
    )
    if turn.status == "processing":
        return [user]
    assistant = TurnSummary(
        turn_id=turn.turn_id,
        role="assistant",
        content=_assistant_summary_content(turn),
        status=cast(TurnStatus, turn.status),
        created_at=turn.created_at,
    )
    return [user, assistant]


def _to_slot_state(turn: Turn | None) -> SlotState | None:
    if turn is None or not turn.slot_state_json:
        return None
    payload = _parse_json_object(turn.slot_state_json)
    if payload is None:
        return None
    return SlotState.model_validate(payload)


def _to_confirmation_summary(row: Confirmation | None) -> ConfirmationSummary | None:
    if row is None:
        return None
    try:
        attendees_raw = json.loads(row.attendees_json) if row.attendees_json else []
    except json.JSONDecodeError:
        logger.warning("确认单 attendees_json 无法解析", confirmation_id=row.confirmation_id)
        attendees_raw = []
    attendees = [str(item) for item in attendees_raw] if isinstance(attendees_raw, list) else []
    return ConfirmationSummary(
        confirmation_id=row.confirmation_id,
        turn_id=row.turn_id,
        status=cast(ConfirmationStatus, row.status),
        meeting_time=row.meeting_time,
        attendees=attendees,
        topic=row.topic,
        duration_minutes=row.duration_minutes,
        meeting_type=cast(MeetingType, row.meeting_type),
        slot_snapshot_hash=row.slot_snapshot_hash,
    )


def _to_detail(
    conversation: Conversation,
    turns: list[Turn],
    pending: Confirmation | None,
) -> ConversationDetailResponse:
    last_turn = turns[-1] if turns else None
    summaries: list[TurnSummary] = []
    for item in turns:
        summaries.extend(_to_turn_summaries(item))
    return ConversationDetailResponse(
        conversation_id=conversation.conversation_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        turns=summaries,
        active_slot_state=_to_slot_state(last_turn),
        active_confirmation=_to_confirmation_summary(pending),
    )


class ConversationService:
    def __init__(
        self,
        db: AsyncSession,
        app_settings: AppSettings | None = None,
        repo: ConversationRepository | None = None,
    ) -> None:
        self.db = db
        self.settings = app_settings if app_settings is not None else settings
        self.repo = repo if repo is not None else ConversationRepository(db)

    async def list_conversations(self, user: UserContext, limit: int) -> ConversationListResponse:
        rows = await self.repo.list_by_user(user.user_id, limit)
        total = await self.repo.count_by_user(user.user_id)
        items = [
            ConversationSummary(
                conversation_id=row.conversation_id,
                title=row.title,
                updated_at=row.updated_at,
                preview=row.preview,
            )
            for row in rows
        ]
        return ConversationListResponse(items=items, total=total)

    async def create_conversation(
        self, user: UserContext, title: str | None
    ) -> ConversationDetailResponse:
        now = utc_now_iso()
        resolved_title = title if title else self.settings.conversation_default_title
        conversation_id = _new_conversation_id()
        row = await self.repo.create(
            conversation_id=conversation_id,
            user_id=user.user_id,
            title=resolved_title,
            created_at=now,
            updated_at=now,
        )
        logger.info("已创建对话", conversation_id=conversation_id, user_id=user.user_id)
        return _to_detail(row, [], None)

    async def get_conversation(
        self, user: UserContext, conversation_id: str
    ) -> ConversationDetailResponse:
        row = await self.repo.get_by_id_for_user(conversation_id, user.user_id)
        if row is None:
            raise ConversationNotFoundError("对话不存在")
        turns = await self.repo.list_turns(conversation_id)
        pending = await self.repo.get_pending_confirmation(conversation_id)
        return _to_detail(row, turns, pending)
