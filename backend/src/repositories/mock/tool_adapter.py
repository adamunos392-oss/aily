"""Mock Tool Adapter。People / Calendar / Meeting / WorkMessage / MeetingRoom 原子 Tool。"""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from src.core.config import AppSettings, settings
from src.models.agent.types import MeetingRoomItem, QueryContext, ToolCall, ToolResult
from src.repositories.mock.ids import stable_id

_SHANGHAI = ZoneInfo("Asia/Shanghai")
_XINGHE_DURATION_MINUTES = 180
_QIHANG_DURATION_MINUTES = 90


class ToolAdapter:
    def __init__(self, app_settings: AppSettings | None = None) -> None:
        self._settings = app_settings if app_settings is not None else settings

    async def execute(self, call: ToolCall, query: QueryContext) -> ToolResult:
        if call.tool_id == "people_lookup":
            return self._people_lookup(call)
        if call.tool_id == "calendar_check":
            return ToolResult(
                call_id=call.call_id,
                tool_id=call.tool_id,
                status="success",
                payload={"available": True},
                error_message=None,
            )
        if call.tool_id == "meeting_create":
            return self._meeting_create(call, query)
        if call.tool_id == "work_message_fetch":
            return self._work_messages(call)
        if call.tool_id == "meeting_room_query":
            return self._meeting_rooms(call)
        return ToolResult(
            call_id=call.call_id,
            tool_id=call.tool_id,
            status="failure",
            payload=None,
            error_message=f"未知 tool_id: {call.tool_id}",
        )

    def _people_lookup(self, call: ToolCall) -> ToolResult:
        name = self._settings.meeting_disambiguation_person_name
        department = self._settings.mock_user_department
        payload = {
            "people": [
                {
                    "person_id": "person-zhangming-product",
                    "choice_id": "person:zhangming-product",
                    "display_name": name,
                    "department": department,
                },
                {
                    "person_id": "person-zhangming-finance",
                    "choice_id": "person:zhangming-finance",
                    "display_name": name,
                    "department": "财务部",
                },
            ]
        }
        return ToolResult(
            call_id=call.call_id,
            tool_id=call.tool_id,
            status="success",
            payload=payload,
            error_message=None,
        )

    def _meeting_create(self, call: ToolCall, query: QueryContext) -> ToolResult:
        timeout_id = self._settings.meeting_timeout_demo_conversation_id
        if query.conversation_id == timeout_id:
            return ToolResult(
                call_id=call.call_id,
                tool_id=call.tool_id,
                status="timeout",
                payload=None,
                error_message="原子能力超时",
            )
        meeting_id = stable_id("meeting", self._settings, query.conversation_id, query.turn_id)
        return ToolResult(
            call_id=call.call_id,
            tool_id=call.tool_id,
            status="success",
            payload={"meeting_id": meeting_id, "created": True},
            error_message=None,
        )

    def _work_messages(self, call: ToolCall) -> ToolResult:
        payload = {
            "messages": [
                {"message_id": "msg-work-arch", "kind": "work", "content": "完成 Aily 工作台信息架构评审"},
                {"message_id": "msg-work-zhangming", "kind": "work", "content": "与张明对齐项目复盘会材料"},
                {"message_id": "msg-chitchat-dinner", "kind": "chitchat", "content": "晚上吃啥"},
            ]
        }
        return ToolResult(
            call_id=call.call_id,
            tool_id=call.tool_id,
            status="success",
            payload=payload,
            error_message=None,
        )

    def _meeting_rooms(self, call: ToolCall) -> ToolResult:
        rooms = [item.model_dump() for item in self.demo_rooms()]
        return ToolResult(
            call_id=call.call_id,
            tool_id=call.tool_id,
            status="success",
            payload={"rooms": rooms},
            error_message=None,
        )

    def demo_rooms(self) -> list[MeetingRoomItem]:
        after_hour = self._settings.meeting_room_query_after_hour
        offset_days = self._settings.meeting_room_query_demo_date_offset_days
        seed = self._settings.mock_deterministic_seed
        base_local = datetime(2026, 9, 21, 10, 0, 0, tzinfo=_SHANGHAI) + timedelta(seconds=seed)
        day = (base_local + timedelta(days=offset_days)).date()
        start = datetime(day.year, day.month, day.day, after_hour, 0, 0, tzinfo=_SHANGHAI)

        def window(duration_minutes: int) -> tuple[str, str]:
            end = start + timedelta(minutes=duration_minutes)
            return (
                start.astimezone(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ"),
                end.astimezone(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ"),
            )

        xinghe_from, xinghe_to = window(_XINGHE_DURATION_MINUTES)
        qihang_from, qihang_to = window(_QIHANG_DURATION_MINUTES)
        return [
            MeetingRoomItem(room_name="星河 3 号", available_from=xinghe_from, available_to=xinghe_to),
            MeetingRoomItem(room_name="启航厅", available_from=qihang_from, available_to=qihang_to),
        ]
