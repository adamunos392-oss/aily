"""Mock Slot Adapter。槽位提取 / 补全 / 关键槽变更检测。"""

from __future__ import annotations

import hashlib
import json
import re

from src.core.config import AppSettings, settings
from src.models.agent.types import (
    ChoiceOption,
    ConversationRuntimeState,
    IntentResult,
    QueryContext,
    SlotAdapterResult,
    SlotState,
    SlotValue,
)

_TIME_HINT = re.compile(r"点|下午|上午|明天|今晚|:\d{2}")
_TWO_OCLOCK = re.compile(r"两\s*点|14\s*[:：]00")
_PRODUCT_CHOICE_ID = "person:zhangming-product"
_FINANCE_CHOICE_ID = "person:zhangming-finance"


def slot_snapshot_hash(slot_state: SlotState, app_settings: AppSettings) -> str:
    payload = json.dumps(
        {
            "seed": app_settings.mock_deterministic_seed,
            "slots": slot_state.slots,
            "missing": slot_state.missing_required,
        },
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


class SlotAdapter:
    def __init__(self, app_settings: AppSettings | None = None) -> None:
        self._settings = app_settings if app_settings is not None else settings

    async def fill(
        self,
        query: QueryContext,
        intent: IntentResult,
        rewritten_query: str,
        conversation_state: ConversationRuntimeState,
    ) -> SlotAdapterResult:
        if intent.intent != "create_meeting":
            empty = SlotState(slots={}, missing_required=[], is_complete=True)
            return SlotAdapterResult(slot_state=empty)

        text = f"{query.raw_query} {rewritten_query}"
        person_name = self._settings.meeting_disambiguation_person_name
        previous = conversation_state.slot_state
        previous_slots: dict[str, SlotValue] = previous.slots if previous is not None else {}

        meeting_time = self._extract_time(text, previous_slots.get("meeting_time"))
        topic = self._extract_topic(text, previous_slots.get("topic"))
        attendees = self._extract_attendees(text, person_name, previous_slots.get("attendees"))
        selected = conversation_state.choice_id or previous_slots.get("selected_person_id")
        if isinstance(selected, list):
            selected = selected[0] if selected else None

        duration = previous_slots.get("duration_minutes")
        if duration is None:
            duration = str(self._settings.meeting_default_duration_minutes)
        meeting_type = previous_slots.get("meeting_type") or self._settings.meeting_default_type

        slots: dict[str, SlotValue] = {
            "meeting_time": meeting_time,
            "attendees": attendees,
            "topic": topic,
            "duration_minutes": str(duration),
            "meeting_type": str(meeting_type),
            "selected_person_id": selected if isinstance(selected, str) else None,
        }

        missing: list[str] = []
        if not meeting_time:
            missing.append("meeting_time")
        if not attendees:
            missing.append("attendees")
        if not topic:
            missing.append("topic")

        needs_disambiguation = bool(
            person_name in text and not slots["selected_person_id"] and attendees
        )
        is_complete = not missing and not needs_disambiguation

        current = SlotState(slots=slots, missing_required=missing, is_complete=is_complete)
        key_slot_changed = bool(
            previous is not None
            and previous.slots.get("meeting_time")
            and meeting_time
            and previous.slots.get("meeting_time") != meeting_time
        )
        choices: list[ChoiceOption] = []
        if needs_disambiguation:
            department = self._settings.mock_user_department
            choices = [
                ChoiceOption(choice_id=_PRODUCT_CHOICE_ID, label=f"{person_name} · {department}"),
                ChoiceOption(choice_id=_FINANCE_CHOICE_ID, label=f"{person_name} · 财务部"),
            ]
        return SlotAdapterResult(
            slot_state=current,
            key_slot_changed=key_slot_changed,
            needs_disambiguation=needs_disambiguation,
            choices=choices,
        )

    def _extract_time(self, text: str, previous: SlotValue) -> str | None:
        if _TWO_OCLOCK.search(text):
            return "明天下午 14:00"
        if _TIME_HINT.search(text):
            return "明天下午 15:00"
        if isinstance(previous, str) and previous:
            return previous
        return None

    def _extract_topic(self, text: str, previous: SlotValue) -> str | None:
        if "复盘" in text:
            return "项目复盘会"
        if isinstance(previous, str) and previous:
            return previous
        if "会议" in text or "开会" in text:
            return "会议"
        return None

    def _extract_attendees(
        self, text: str, person_name: str, previous: SlotValue
    ) -> list[str] | None:
        names: list[str] = []
        if person_name in text:
            names.append(person_name)
        if isinstance(previous, list):
            for item in previous:
                if item not in names:
                    names.append(item)
        elif isinstance(previous, str) and previous and previous not in names:
            names.append(previous)
        return names or None
