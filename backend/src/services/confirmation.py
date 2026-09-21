"""确认单：同意执行写链、取消、关键槽更新作废旧单。"""

from __future__ import annotations

import json
from typing import Any, cast

from pycore.core import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import AppSettings, settings
from src.db.models import Confirmation, Meeting, utc_now_iso
from src.db.models import TraceEvent as TraceEventRow
from src.models.agent.types import (
    AssistantMessage,
    ConfirmationSummary,
    ConversationRuntimeState,
    IntentResult,
    QueryContext,
    RouteDecision,
    SlotAdapterResult,
    SlotState,
    TurnResponse,
    to_iso_z,
)
from src.repositories.conversation import ConversationRepository
from src.repositories.mock.ids import make_trace_event, stable_id
from src.repositories.mock.slot_adapter import SlotAdapter, slot_snapshot_hash
from src.repositories.turn import TurnRepository
from src.services.agent_nodes import ResultValidationService, SkillService
from src.services.turn import (
    TurnNotFoundError,
    TurnService,
    _dump_json,
)

logger = get_logger()


class ConfirmationNotFoundError(FileNotFoundError):
    """确认单不存在。"""


class ConfirmationConflictError(PermissionError):
    """确认单状态不允许当前操作。"""


class SlotUpdateNotAllowedError(PermissionError):
    """当前轮次不允许修改会议槽位。"""


class TurnIdMismatchError(ValueError):
    """turn_id 与确认单不匹配。"""


class EmptySlotUpdatesError(ValueError):
    """updates 为空。"""


def _clock_label(value: object) -> str:
    text = str(value or "")
    if "14:00" in text:
        return "14:00"
    if "15:00" in text:
        return "15:00"
    return text or "—"


class ConfirmationService:
    def __init__(
        self,
        db: AsyncSession,
        app_settings: AppSettings | None = None,
        conversation_repo: ConversationRepository | None = None,
        turn_repo: TurnRepository | None = None,
        turn_service: TurnService | None = None,
    ) -> None:
        self.db = db
        self.settings = app_settings if app_settings is not None else settings
        self.conversations = (
            conversation_repo if conversation_repo is not None else ConversationRepository(db)
        )
        self.turns = turn_repo if turn_repo is not None else TurnRepository(db)
        self.turns_svc = turn_service if turn_service is not None else TurnService(db, self.settings)

    async def approve(
        self, user: Any, conversation_id: str, confirmation_id: str, turn_id: str
    ) -> TurnResponse:
        conversation = await self.turns_svc._require_owned_conversation(user, conversation_id)
        row = await self.conversations.get_confirmation(conversation_id, confirmation_id)
        if row is None:
            raise ConfirmationNotFoundError("确认单不存在")
        if row.status != "pending":
            raise ConfirmationConflictError("确认单已失效，请重新确认")
        if row.turn_id != turn_id:
            raise TurnIdMismatchError("turn_id 与确认单不匹配")
        turn = await self.turns.get_by_id(conversation_id, turn_id)
        if turn is None:
            raise TurnNotFoundError("轮次不存在")

        now = utc_now_iso()
        row.status = "approved"
        row.updated_at = now
        await self.db.flush()

        slot_state = (
            SlotState.model_validate(json.loads(turn.slot_state_json))
            if turn.slot_state_json
            else SlotState(slots={}, missing_required=[], is_complete=True)
        )
        selected = slot_state.slots.get("selected_person_id")
        choice_id = selected if isinstance(selected, str) else None
        query = QueryContext(
            conversation_id=conversation_id,
            turn_id=turn_id,
            raw_query=turn.content,
            entry_source=cast(Any, turn.entry_source or "manual"),
            user_id=user.user_id,
        )
        runtime = ConversationRuntimeState(
            slot_state=slot_state,
            choice_id=choice_id,
            execute_write=True,
        )
        intent = IntentResult(intent="create_meeting", operation_type="WRITE", confidence=1.0)
        slot_result = SlotAdapterResult(
            slot_state=slot_state, needs_disambiguation=False
        )
        skill_service = SkillService()
        skill = await skill_service.plan(query, intent, slot_result, runtime)
        tool_results = await skill_service.run_tools(skill.tool_calls, query)
        route = RouteDecision(
            route_type="SKILL",
            target=self.settings.create_meeting_skill_id,
            display_route="创建会议技能",
        )
        validation = await ResultValidationService().validate(
            route=route, rag=None, skill=skill, tool_results=tool_results
        )
        summary = self._summary_from_row(row)
        summary.status = "approved"
        assistant = validation.assistant_message.model_copy(update={"confirmation": summary})
        if assistant.message_type == "meeting_success":
            assistant = assistant.model_copy(
                update={
                    "text": "会议已创建。",
                    "confirmation": summary,
                }
            )

        sequence = await self._next_sequence(turn_id)
        events = [
            ("confirmation", "确认", "状态：已同意", {"confirmation_id": confirmation_id, "status": "approved"}),
        ]
        for result in tool_results:
            title, event_summary = self._tool_event(result)
            events.append(
                (
                    "tool_call",
                    title,
                    event_summary,
                    {"tool_id": result.tool_id, "status": result.status},
                )
            )
        result_zh = "未知" if validation.status == "unknown" else "成功"
        events.append(
            (
                "result_validate",
                "结果核验",
                result_zh,
                {"status": validation.status, "result_status": validation.result_status},
            )
        )
        final_summary = (
            "未知 · 待核验"
            if validation.status == "unknown"
            else "已回复 · 会议已创建"
        )
        events.append(("final", "最终结果", final_summary, {"status": validation.status}))
        for node, title_zh, event_summary, payload in events:
            sequence += 1
            self._add_event(turn_id, sequence, node, title_zh, event_summary, payload)

        if validation.status == "replied" and assistant.message_type == "meeting_success":
            meeting_id = None
            for item in tool_results:
                if item.tool_id == "meeting_create" and item.payload:
                    meeting_id = item.payload.get("meeting_id")
            if not isinstance(meeting_id, str) or not meeting_id:
                meeting_id = stable_id("meeting", self.settings, conversation_id, turn_id)
            self.db.add(
                Meeting(
                    meeting_id=meeting_id,
                    conversation_id=conversation_id,
                    confirmation_id=confirmation_id,
                    topic=row.topic,
                    meeting_time=row.meeting_time,
                    attendees_json=row.attendees_json,
                    created_at=now,
                )
            )

        turn.status = validation.status
        turn.assistant_message_type = assistant.message_type
        turn.assistant_payload_json = _dump_json(assistant.model_dump(mode="json"))
        turn.updated_at = now
        conversation.updated_at = now
        await self.db.flush()
        logger.info(
            "确认单已执行",
            confirmation_id=confirmation_id,
            status=validation.status,
        )
        return await self.turns_svc.get_turn(user, conversation_id, turn_id)

    async def cancel(
        self, user: Any, conversation_id: str, confirmation_id: str, turn_id: str
    ) -> TurnResponse:
        conversation = await self.turns_svc._require_owned_conversation(user, conversation_id)
        row = await self.conversations.get_confirmation(conversation_id, confirmation_id)
        if row is None:
            raise ConfirmationNotFoundError("确认单不存在")
        if row.status != "pending":
            raise ConfirmationConflictError("确认单不可取消")
        if row.turn_id != turn_id:
            raise TurnIdMismatchError("turn_id 与确认单不匹配")
        turn = await self.turns.get_by_id(conversation_id, turn_id)
        if turn is None:
            raise TurnNotFoundError("轮次不存在")

        now = utc_now_iso()
        row.status = "cancelled"
        row.updated_at = now
        summary = self._summary_from_row(row)
        assistant = AssistantMessage(
            message_type="text",
            text="已取消创建会议，未创建会议。",
            confirmation=summary,
        )
        sequence = await self._next_sequence(turn_id)
        self._add_event(
            turn_id,
            sequence + 1,
            "confirmation",
            "确认",
            "状态：已取消",
            {"confirmation_id": confirmation_id, "status": "cancelled"},
        )
        self._add_event(
            turn_id,
            sequence + 2,
            "final",
            "最终结果",
            "已取消 · 未创建会议",
            {"status": "replied"},
        )
        turn.status = "replied"
        turn.assistant_message_type = "text"
        turn.assistant_payload_json = _dump_json(assistant.model_dump(mode="json"))
        turn.updated_at = now
        conversation.updated_at = now
        await self.db.flush()
        return await self.turns_svc.get_turn(user, conversation_id, turn_id)

    async def update_slots(
        self, user: Any, conversation_id: str, turn_id: str, updates: dict[str, str]
    ) -> TurnResponse:
        if not updates:
            raise EmptySlotUpdatesError("updates 不能为空")
        conversation = await self.turns_svc._require_owned_conversation(user, conversation_id)
        turn = await self.turns.get_by_id(conversation_id, turn_id)
        if turn is None:
            raise TurnNotFoundError("轮次不存在")
        if turn.intent != "create_meeting":
            raise SlotUpdateNotAllowedError("当前轮次不允许修改会议槽位")
        if not turn.slot_state_json:
            raise SlotUpdateNotAllowedError("当前轮次不允许修改会议槽位")

        slot_state = SlotState.model_validate(json.loads(turn.slot_state_json))
        adapter = SlotAdapter(self.settings)
        old_time = str(slot_state.slots.get("meeting_time") or "")
        if "meeting_time" in updates:
            extracted = adapter.normalize_meeting_time(updates["meeting_time"], old_time)
            slot_state.slots["meeting_time"] = extracted or updates["meeting_time"]
        for key, value in updates.items():
            if key != "meeting_time":
                slot_state.slots[key] = value
        slot_state.missing_required = []
        slot_state.is_complete = True

        pending = await self.conversations.get_pending_confirmation(conversation_id)
        now = utc_now_iso()
        if pending is not None:
            pending.status = "invalidated"
            pending.updated_at = now
            await self.db.flush()

        new_time = str(slot_state.slots.get("meeting_time") or "明天下午 15:00")
        attendees_raw = slot_state.slots.get("attendees")
        attendees = (
            [str(item) for item in attendees_raw]
            if isinstance(attendees_raw, list)
            else ([str(attendees_raw)] if attendees_raw else [])
        )
        duration_raw = slot_state.slots.get("duration_minutes")
        duration = (
            int(duration_raw)
            if isinstance(duration_raw, str) and duration_raw.isdigit()
            else self.settings.meeting_default_duration_minutes
        )
        meeting_type = slot_state.slots.get("meeting_type") or self.settings.meeting_default_type
        typed = meeting_type if meeting_type in {"online", "offline"} else self.settings.meeting_default_type
        new_id = stable_id("cfm", self.settings, turn_id, new_time)
        summary = ConfirmationSummary(
            confirmation_id=new_id,
            turn_id=turn_id,
            status="pending",
            meeting_time=new_time,
            attendees=attendees,
            topic=str(slot_state.slots.get("topic") or ""),
            duration_minutes=duration,
            meeting_type=cast(Any, typed),
            slot_snapshot_hash=slot_snapshot_hash(slot_state, self.settings),
        )
        self.db.add(
            Confirmation(
                confirmation_id=summary.confirmation_id,
                conversation_id=conversation_id,
                turn_id=turn_id,
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
        assistant = AssistantMessage(
            message_type="confirmation",
            text="请重新确认",
            confirmation=summary,
        )
        sequence = await self._next_sequence(turn_id)
        self._add_event(
            turn_id,
            sequence + 1,
            "slot_fill",
            "槽位填充",
            f"会议时间由 {_clock_label(old_time)} 改为 {_clock_label(new_time)}",
            {"meeting_time": new_time},
        )
        self._add_event(
            turn_id,
            sequence + 2,
            "confirmation",
            "确认",
            "原确认已作废",
            {
                "confirmation_id": pending.confirmation_id if pending is not None else "",
                "status": "invalidated",
                "meeting_time": _clock_label(old_time),
            },
        )
        self._add_event(
            turn_id,
            sequence + 3,
            "confirmation",
            "确认",
            "状态：待确认",
            {"confirmation_id": new_id, "status": "pending"},
        )
        self._add_event(
            turn_id,
            sequence + 4,
            "final",
            "最终结果",
            "待确认 · 尚未创建",
            {"status": "awaiting_confirmation"},
        )
        turn.status = "awaiting_confirmation"
        turn.assistant_message_type = "confirmation"
        turn.assistant_payload_json = _dump_json(assistant.model_dump(mode="json"))
        turn.slot_state_json = _dump_json(slot_state.model_dump(mode="json"))
        turn.updated_at = now
        conversation.updated_at = now
        await self.db.flush()
        return await self.turns_svc.get_turn(user, conversation_id, turn_id)

    def _summary_from_row(self, row: Confirmation) -> ConfirmationSummary:
        attendees_raw = json.loads(row.attendees_json) if row.attendees_json else []
        attendees = [str(item) for item in attendees_raw] if isinstance(attendees_raw, list) else []
        return ConfirmationSummary(
            confirmation_id=row.confirmation_id,
            turn_id=row.turn_id,
            status=cast(Any, row.status),
            meeting_time=row.meeting_time,
            attendees=attendees,
            topic=row.topic,
            duration_minutes=row.duration_minutes,
            meeting_type=cast(Any, row.meeting_type),
            slot_snapshot_hash=row.slot_snapshot_hash,
        )

    async def _next_sequence(self, turn_id: str) -> int:
        events = await self.turns.list_trace_events(turn_id)
        if not events:
            return 0
        return max(item.sequence for item in events)

    def _add_event(
        self,
        turn_id: str,
        sequence: int,
        node: str,
        title_zh: str,
        summary: str,
        payload: dict[str, Any],
    ) -> None:
        event = make_trace_event(
            turn_id=turn_id,
            sequence=sequence,
            node=cast(Any, node),
            title_zh=title_zh,
            summary=summary,
            payload=payload,
        )
        self.db.add(
            TraceEventRow(
                event_id=event.event_id,
                turn_id=event.turn_id,
                sequence=event.sequence,
                occurred_at=to_iso_z(event.occurred_at)
                if hasattr(event.occurred_at, "strftime")
                else str(event.occurred_at).replace("+00:00", "Z"),
                node=event.node,
                title_zh=event.title_zh,
                summary=event.summary,
                payload_json=_dump_json(event.payload),
            )
        )

    @staticmethod
    def _tool_event(result: Any) -> tuple[str, str]:
        if result.status == "timeout":
            return "原子能力超时", "创建会议超时"
        if result.tool_id == "people_lookup":
            return "原子能力", "找人成功"
        if result.tool_id == "calendar_check":
            return "原子能力", "日历可写"
        if result.tool_id == "meeting_create":
            return "原子能力", "会议已写入"
        return "工具调用", str(result.status)
