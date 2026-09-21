"""Mock Skill Adapter。create_meeting / generate_work_report 固定编排。"""

from src.core.config import AppSettings, settings
from src.models.agent.types import (
    ConfirmationSummary,
    ConversationRuntimeState,
    IntentResult,
    QueryContext,
    ReportDraft,
    SkillAdapterResult,
    SlotAdapterResult,
    ToolCall,
)
from src.repositories.mock.ids import stable_id
from src.repositories.mock.slot_adapter import slot_snapshot_hash


class SkillAdapter:
    def __init__(self, app_settings: AppSettings | None = None) -> None:
        self._settings = app_settings if app_settings is not None else settings

    async def plan(
        self,
        query: QueryContext,
        intent: IntentResult,
        slot_result: SlotAdapterResult,
        conversation_state: ConversationRuntimeState,
    ) -> SkillAdapterResult:
        if intent.intent == "generate_work_report":
            return self._weekly_report(query)
        return self._create_meeting(query, slot_result, conversation_state)

    def _weekly_report(self, query: QueryContext) -> SkillAdapterResult:
        call_id = stable_id("call", self._settings, query.turn_id, "work_message_fetch")
        draft_id = stable_id("draft", self._settings, query.turn_id)
        draft = ReportDraft(
            draft_id=draft_id,
            skill_name="生成工作周报",
            content=(
                "本周工作周报（林小北）\n"
                "1. 完成 Aily 工作台信息架构评审\n"
                "2. 与张明对齐项目复盘会材料"
            ),
            is_edited=False,
        )
        return SkillAdapterResult(
            skill_id=self._settings.weekly_report_skill_id,
            status="replied",
            tool_calls=[
                ToolCall(tool_id="work_message_fetch", arguments={"week": "current"}, call_id=call_id)
            ],
            report_draft=draft,
            message_type="report_draft",
            text=None,
        )

    def _create_meeting(
        self,
        query: QueryContext,
        slot_result: SlotAdapterResult,
        conversation_state: ConversationRuntimeState,
    ) -> SkillAdapterResult:
        skill_id = self._settings.create_meeting_skill_id
        if slot_result.slot_state.missing_required:
            missing = "、".join(slot_result.slot_state.missing_required)
            return SkillAdapterResult(
                skill_id=skill_id,
                status="clarifying",
                message_type="clarification",
                text=f"还需要补充：{missing}",
            )
        if slot_result.needs_disambiguation:
            return SkillAdapterResult(
                skill_id=skill_id,
                status="clarifying",
                message_type="disambiguation",
                text=f"有多名{self._settings.meeting_disambiguation_person_name}，请选择一位。",
                choices=slot_result.choices,
            )
        if conversation_state.execute_write:
            call_id = stable_id("call", self._settings, query.turn_id, "meeting_create")
            return SkillAdapterResult(
                skill_id=skill_id,
                status="processing",
                tool_calls=[
                    ToolCall(
                        tool_id="meeting_create",
                        arguments={"topic": str(slot_result.slot_state.slots.get("topic") or "")},
                        call_id=call_id,
                    )
                ],
                message_type="text",
            )
        confirmation = self._pending_confirmation(query, slot_result)
        return SkillAdapterResult(
            skill_id=skill_id,
            status="awaiting_confirmation",
            confirmation=confirmation,
            message_type="confirmation",
            text="请确认创建会议",
        )

    def _pending_confirmation(
        self, query: QueryContext, slot_result: SlotAdapterResult
    ) -> ConfirmationSummary:
        slots = slot_result.slot_state.slots
        attendees = slots.get("attendees")
        names = attendees if isinstance(attendees, list) else ([attendees] if attendees else [])
        duration_raw = slots.get("duration_minutes")
        duration = (
            int(duration_raw)
            if isinstance(duration_raw, str) and duration_raw.isdigit()
            else self._settings.meeting_default_duration_minutes
        )
        meeting_type = slots.get("meeting_type")
        typed = meeting_type if meeting_type in {"online", "offline"} else self._settings.meeting_default_type
        return ConfirmationSummary(
            confirmation_id=stable_id("cfm", self._settings, query.turn_id),
            turn_id=query.turn_id,
            status="pending",
            meeting_time=str(slots.get("meeting_time") or ""),
            attendees=[str(item) for item in names if item],
            topic=str(slots.get("topic") or ""),
            duration_minutes=duration,
            meeting_type=typed,  # type: ignore[arg-type]
            slot_snapshot_hash=slot_snapshot_hash(slot_result.slot_state, self._settings),
        )
