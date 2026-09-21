"""Mock Skill Adapter。create_meeting / generate_work_report 固定编排。"""

from src.core.config import AppSettings, settings
from src.models.agent.types import (
    ConfirmationSummary,
    ConversationRuntimeState,
    IntentResult,
    MemoryState,
    QueryContext,
    ReportDraft,
    SkillAdapterResult,
    SlotAdapterResult,
    ToolCall,
    ToolResult,
)
from src.repositories.mock.ids import stable_id
from src.repositories.mock.slot_adapter import slot_snapshot_hash

WEEKLY_REPORT_INTRO = "已命中技能：生成工作周报。按固定步骤生成本周周报，事实来自本轮工作消息。"
WEEKLY_REPORT_SKILL_NAME = "生成工作周报"


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
        return SkillAdapterResult(
            skill_id=self._settings.weekly_report_skill_id,
            status="replied",
            tool_calls=[
                ToolCall(tool_id="work_message_fetch", arguments={"week": "current"}, call_id=call_id)
            ],
            report_draft=None,
            message_type="report_draft",
            text=WEEKLY_REPORT_INTRO,
        )

    def compose_weekly_report(
        self,
        query: QueryContext,
        tool_results: list[ToolResult],
        memory: MemoryState,
    ) -> ReportDraft:
        work_items = self._work_items_from_tools(tool_results)
        content = self._render_weekly_report(work_items, memory)
        return ReportDraft(
            draft_id=stable_id("draft", self._settings, query.turn_id),
            skill_name=WEEKLY_REPORT_SKILL_NAME,
            content=content,
            is_edited=False,
        )

    def _work_items_from_tools(self, tool_results: list[ToolResult]) -> list[str]:
        messages: list[object] = []
        for result in tool_results:
            if result.tool_id != "work_message_fetch":
                continue
            payload = result.payload or {}
            raw = payload.get("messages")
            if isinstance(raw, list):
                messages.extend(raw)
        items: list[str] = []
        for row in messages:
            if not isinstance(row, dict):
                continue
            if row.get("kind") != "work":
                continue
            text = str(row.get("content") or "").strip()
            if text:
                items.append(text)
        return items

    def _render_weekly_report(self, work_items: list[str], memory: MemoryState) -> str:
        name = self._settings.mock_user_display_name
        header = f"本周工作周报（{name}）" if memory.language == "zh-CN" else f"Weekly report ({name})"
        if memory.template_style == "bullet_list":
            numbered = [f"{index}. {item}" for index, item in enumerate(work_items, start=1)]
            body = "\n".join(numbered)
        else:
            body = "\n".join(work_items)
        return header if not body else f"{header}\n{body}"

    def _create_meeting(
        self,
        query: QueryContext,
        slot_result: SlotAdapterResult,
        conversation_state: ConversationRuntimeState,
    ) -> SkillAdapterResult:
        skill_id = self._settings.create_meeting_skill_id
        if slot_result.slot_state.missing_required:
            if "meeting_time" in slot_result.slot_state.missing_required:
                text = "还需要补全会议时间。请问安排在哪一天、几点？"
            else:
                missing = "、".join(slot_result.slot_state.missing_required)
                text = f"还需要补充：{missing}"
            return SkillAdapterResult(
                skill_id=skill_id,
                status="clarifying",
                message_type="clarification",
                text=text,
            )
        if slot_result.needs_disambiguation:
            name = self._settings.meeting_disambiguation_person_name
            return SkillAdapterResult(
                skill_id=skill_id,
                status="clarifying",
                message_type="disambiguation",
                text=f"通讯录里有两位{name}，请选择具体的人：",
                choices=slot_result.choices,
            )
        if conversation_state.execute_write:
            return SkillAdapterResult(
                skill_id=skill_id,
                status="processing",
                tool_calls=[
                    ToolCall(
                        tool_id="people_lookup",
                        arguments={"name": self._settings.meeting_disambiguation_person_name},
                        call_id=stable_id("call", self._settings, query.turn_id, "people_lookup"),
                    ),
                    ToolCall(
                        tool_id="calendar_check",
                        arguments={},
                        call_id=stable_id("call", self._settings, query.turn_id, "calendar_check"),
                    ),
                    ToolCall(
                        tool_id="meeting_create",
                        arguments={"topic": str(slot_result.slot_state.slots.get("topic") or "")},
                        call_id=stable_id("call", self._settings, query.turn_id, "meeting_create"),
                    ),
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
