"""一轮提问：走固定 Agent 编排并落库 turns / citations / trace_events。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, cast

from pycore.core import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import AppSettings, settings
from src.db.models import Citation as CitationRow
from src.db.models import Confirmation, Conversation, Turn, utc_now_iso
from src.db.models import ReportDraft as ReportDraftRow
from src.db.models import TraceEvent as TraceEventRow
from src.models.agent.types import (
    AssistantMessage,
    Citation,
    ConfirmationSummary,
    ConversationRuntimeState,
    EntrySource,
    IntentResult,
    QueryContext,
    ReportDraft,
    RouteDecision,
    SlotState,
    TraceEvent,
    TurnResponse,
    TurnStatus,
    to_iso_z,
)
from src.models.user_context import UserContext
from src.repositories.conversation import ConversationRepository
from src.repositories.turn import TurnRepository
from src.services.agent_orchestrator import AgentOrchestratorService
from src.services.conversation import ConversationNotFoundError

logger = get_logger()


class ConversationForbiddenError(PermissionError):
    """对话存在但不属于当前身份。"""


class TurnNotFoundError(FileNotFoundError):
    """轮次不存在。"""


class EmptyTurnContentError(ValueError):
    """content 为空。"""


def _new_turn_id() -> str:
    return f"turn-{uuid.uuid4().hex[:12]}"


def _parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _dump_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False)


class TurnService:
    def __init__(
        self,
        db: AsyncSession,
        app_settings: AppSettings | None = None,
        conversation_repo: ConversationRepository | None = None,
        turn_repo: TurnRepository | None = None,
        orchestrator: AgentOrchestratorService | None = None,
    ) -> None:
        self.db = db
        self.settings = app_settings if app_settings is not None else settings
        self.conversations = (
            conversation_repo if conversation_repo is not None else ConversationRepository(db)
        )
        self.turns = turn_repo if turn_repo is not None else TurnRepository(db)
        self.orchestrator = (
            orchestrator if orchestrator is not None else AgentOrchestratorService()
        )

    async def create_turn(
        self,
        user: UserContext,
        conversation_id: str,
        *,
        content: str,
        entry_source: EntrySource,
        choice_id: str | None,
        client_turn_key: str | None,
    ) -> TurnResponse:
        text = content.strip()
        if not text:
            raise EmptyTurnContentError("content 不能为空")
        conversation = await self._require_owned_conversation(user, conversation_id)
        if client_turn_key:
            existing = await self.turns.get_by_client_key(conversation_id, client_turn_key)
            if existing is not None:
                return await self._to_response(existing)
        runtime = await self._runtime_state(conversation_id, choice_id)
        turn_id = _new_turn_id()
        query = QueryContext(
            conversation_id=conversation_id,
            turn_id=turn_id,
            raw_query=text,
            entry_source=entry_source,
            user_id=user.user_id,
        )
        result = await self.orchestrator.run(query, runtime)
        now = utc_now_iso()
        row = Turn(
            turn_id=result.turn_id,
            conversation_id=conversation_id,
            client_turn_key=client_turn_key,
            role="user",
            content=text,
            entry_source=entry_source,
            status=result.status,
            intent=result.intent.intent,
            operation_type=result.intent.operation_type,
            route_type=result.route_decision.route_type,
            route_target=result.route_decision.target,
            display_route=result.route_decision.display_route,
            assistant_message_type=result.assistant_message.message_type,
            assistant_payload_json=_dump_json(result.assistant_message.model_dump(mode="json")),
            slot_state_json=(
                _dump_json(result.slot_state.model_dump(mode="json"))
                if result.slot_state is not None
                else None
            ),
            choice_id=choice_id,
            created_at=now,
            updated_at=now,
        )
        self.db.add(row)
        await self.db.flush()
        self._add_citations(result)
        self._add_trace_events(result)
        await self._sync_confirmation(conversation_id, result)
        await self._sync_report_draft(result)
        conversation.preview = text
        conversation.updated_at = now
        if conversation.title == self.settings.conversation_default_title:
            conversation.title = text[:40]
        await self.db.flush()
        logger.info(
            "已创建一轮提问",
            conversation_id=conversation_id,
            turn_id=result.turn_id,
            status=result.status,
        )
        return result

    async def get_turn(
        self, user: UserContext, conversation_id: str, turn_id: str
    ) -> TurnResponse:
        await self._require_owned_conversation(user, conversation_id)
        row = await self.turns.get_by_id(conversation_id, turn_id)
        if row is None:
            raise TurnNotFoundError("轮次不存在")
        return await self._to_response(row)

    async def _require_owned_conversation(
        self, user: UserContext, conversation_id: str
    ) -> Conversation:
        row = await self.conversations.get_by_id(conversation_id)
        if row is None:
            raise ConversationNotFoundError("对话不存在")
        if row.user_id != user.user_id:
            raise ConversationForbiddenError("对话不属于当前身份")
        return row

    async def _runtime_state(
        self, conversation_id: str, choice_id: str | None
    ) -> ConversationRuntimeState:
        pending = await self.conversations.get_pending_confirmation(conversation_id)
        turns = await self.conversations.list_turns(conversation_id)
        last = turns[-1] if turns else None
        slot_state: SlotState | None = None
        if last is not None and last.slot_state_json:
            slot_state = SlotState.model_validate(json.loads(last.slot_state_json))
        confirmation = None
        if pending is not None:
            attendees_raw = json.loads(pending.attendees_json) if pending.attendees_json else []
            attendees = [str(item) for item in attendees_raw] if isinstance(attendees_raw, list) else []
            confirmation = ConfirmationSummary(
                confirmation_id=pending.confirmation_id,
                turn_id=pending.turn_id,
                status=cast(Any, pending.status),
                meeting_time=pending.meeting_time,
                attendees=attendees,
                topic=pending.topic,
                duration_minutes=pending.duration_minutes,
                meeting_type=cast(Any, pending.meeting_type),
                slot_snapshot_hash=pending.slot_snapshot_hash,
            )
        return ConversationRuntimeState(
            slot_state=slot_state,
            active_confirmation=confirmation,
            choice_id=choice_id,
        )

    def _add_citations(self, result: TurnResponse) -> None:
        now = utc_now_iso()
        for index, item in enumerate(result.citations):
            score = 1.0 - index * 0.01
            self.db.add(
                CitationRow(
                    turn_id=result.turn_id,
                    knowledge_entry_id=item.knowledge_entry_id,
                    document_title=item.document_title,
                    section=item.section,
                    excerpt=item.excerpt,
                    score=score,
                    created_at=now,
                )
            )

    def _add_trace_events(self, result: TurnResponse) -> None:
        for event in result.trace_events:
            self.db.add(
                TraceEventRow(
                    event_id=event.event_id,
                    turn_id=event.turn_id,
                    sequence=event.sequence,
                    occurred_at=to_iso_z(event.occurred_at)
                    if isinstance(event.occurred_at, datetime)
                    else str(event.occurred_at),
                    node=event.node,
                    title_zh=event.title_zh,
                    summary=event.summary,
                    payload_json=_dump_json(event.payload),
                )
            )

    async def _sync_confirmation(self, conversation_id: str, result: TurnResponse) -> None:
        pending = await self.conversations.get_pending_confirmation(conversation_id)
        summary = result.assistant_message.confirmation
        now = utc_now_iso()
        if pending is not None and (
            summary is None or pending.confirmation_id != summary.confirmation_id
        ):
            pending.status = "invalidated"
            pending.updated_at = now
            await self.db.flush()
        if summary is None or summary.status != "pending":
            return
        existing = await self.conversations.get_confirmation(conversation_id, summary.confirmation_id)
        if existing is not None:
            return
        self.db.add(
            Confirmation(
                confirmation_id=summary.confirmation_id,
                conversation_id=conversation_id,
                turn_id=result.turn_id,
                status="pending",
                meeting_time=summary.meeting_time,
                attendees_json=_dump_json(summary.attendees),
                topic=summary.topic,
                duration_minutes=summary.duration_minutes,
                meeting_type=summary.meeting_type,
                slot_snapshot_hash=summary.slot_snapshot_hash,
                created_at=now,
                updated_at=now,
            )
        )
        await self.db.flush()

    async def _sync_report_draft(self, result: TurnResponse) -> None:
        draft = result.assistant_message.report_draft
        if draft is None:
            return
        existing = await self.turns.get_report_draft(result.turn_id, draft.draft_id)
        if existing is not None:
            return
        now = utc_now_iso()
        self.db.add(
            ReportDraftRow(
                draft_id=draft.draft_id,
                turn_id=result.turn_id,
                skill_name=draft.skill_name,
                content=draft.content,
                is_edited=1 if draft.is_edited else 0,
                created_at=now,
                updated_at=now,
            )
        )
        await self.db.flush()

    async def _to_response(self, row: Turn) -> TurnResponse:
        payload = json.loads(row.assistant_payload_json) if row.assistant_payload_json else {}
        assistant = AssistantMessage.model_validate(payload) if payload else AssistantMessage(
            message_type="empty"
        )
        stored_draft = await self.turns.get_report_draft(row.turn_id)
        if stored_draft is not None:
            assistant.report_draft = ReportDraft(
                draft_id=stored_draft.draft_id,
                skill_name=stored_draft.skill_name,
                content=stored_draft.content,
                is_edited=bool(stored_draft.is_edited),
            )
        citations_rows = await self.turns.list_citations(row.turn_id)
        citations = [
            Citation(
                document_title=item.document_title,
                section=item.section,
                excerpt=item.excerpt,
                knowledge_entry_id=item.knowledge_entry_id,
            )
            for item in citations_rows
        ]
        events_rows = await self.turns.list_trace_events(row.turn_id)
        events = [
            TraceEvent(
                event_id=item.event_id,
                turn_id=item.turn_id,
                sequence=item.sequence,
                occurred_at=_parse_datetime(item.occurred_at),
                node=cast(Any, item.node),
                title_zh=item.title_zh,
                summary=item.summary,
                payload=json.loads(item.payload_json) if item.payload_json else {},
            )
            for item in events_rows
        ]
        slot_state = None
        if row.slot_state_json:
            slot_state = SlotState.model_validate(json.loads(row.slot_state_json))
        return TurnResponse(
            turn_id=row.turn_id,
            conversation_id=row.conversation_id,
            status=cast(TurnStatus, row.status),
            user_message=row.content,
            assistant_message=assistant,
            citations=citations,
            route_decision=RouteDecision(
                route_type=cast(Any, row.route_type or "RAG"),
                target=row.route_target or "enterprise_knowledge",
                display_route=row.display_route or "企业知识",
            ),
            trace_events=events,
            intent=IntentResult(
                intent=cast(Any, row.intent or "unknown"),
                operation_type=cast(Any, row.operation_type or "READ"),
                confidence=1.0,
            ),
            slot_state=slot_state,
        )
