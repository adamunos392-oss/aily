"""按问句与入口来源做 deterministic 场景分类。取值来自 AppSettings。"""

from __future__ import annotations

from typing import Literal

from src.core.config import AppSettings
from src.models.agent.types import EntrySource, IntentName, OperationType

SceneKind = Literal[
    "travel_qa",
    "refuse_qa",
    "create_meeting",
    "weekly_report",
    "meeting_rooms",
    "unknown",
]

_PROTOTYPE_REFUSE_QUERY = "下季度期权行权价是什么？"
_PROTOTYPE_REFUSE_ALT = "下季度期权行权价是多少？"


def _normalize(text: str) -> str:
    return text.replace("？", "?").strip()


def is_refuse_query(query: str, app_settings: AppSettings) -> bool:
    needle = _normalize(query)
    configured = _normalize(app_settings.knowledge_refuse_demo_query)
    if configured and configured.rstrip("?") in needle:
        return True
    if _normalize(_PROTOTYPE_REFUSE_QUERY).rstrip("?") in needle:
        return True
    if _normalize(_PROTOTYPE_REFUSE_ALT).rstrip("?") in needle:
        return True
    return "期权" in query


def classify_scene(
    query: str,
    entry_source: EntrySource,
    app_settings: AppSettings,
) -> SceneKind:
    if "差旅" in query:
        return "travel_qa"
    if is_refuse_query(query, app_settings):
        return "refuse_qa"
    if "周报" in query or entry_source == "shortcut_report":
        return "weekly_report"
    if "会议室" in query or entry_source == "shortcut_query":
        return "meeting_rooms"
    if (
        "会议" in query
        or "开会" in query
        or app_settings.meeting_disambiguation_person_name in query
        or entry_source in {"shortcut_meeting", "shortcut_task"}
    ):
        return "create_meeting"
    if entry_source == "shortcut_knowledge":
        return "travel_qa"
    return "unknown"


def intent_for_scene(scene: SceneKind) -> tuple[IntentName, OperationType]:
    mapping: dict[SceneKind, tuple[IntentName, OperationType]] = {
        "travel_qa": ("enterprise_knowledge", "READ"),
        "refuse_qa": ("enterprise_knowledge", "READ"),
        "create_meeting": ("create_meeting", "WRITE"),
        "weekly_report": ("generate_work_report", "READ"),
        "meeting_rooms": ("query_meeting_rooms", "READ"),
        "unknown": ("unknown", "READ"),
    }
    return mapping[scene]
