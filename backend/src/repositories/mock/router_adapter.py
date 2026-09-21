"""Mock Router Adapter。按意图产出 RouteDecision。"""

from src.core.config import AppSettings, settings
from src.models.agent.types import EntrySource, IntentResult, RouteDecision
from src.repositories.mock.query_rules import classify_scene


class RouterAdapter:
    def __init__(self, app_settings: AppSettings | None = None) -> None:
        self._settings = app_settings if app_settings is not None else settings

    async def decide(
        self, intent: IntentResult, rewritten_query: str, entry_source: EntrySource
    ) -> RouteDecision:
        scene = classify_scene(rewritten_query, entry_source, self._settings)
        if intent.intent == "create_meeting":
            return RouteDecision(
                route_type="SKILL",
                target=self._settings.create_meeting_skill_id,
                display_route=f"技能 {self._settings.create_meeting_skill_id}",
            )
        if intent.intent == "generate_work_report":
            return RouteDecision(
                route_type="SKILL",
                target=self._settings.weekly_report_skill_id,
                display_route=f"技能 {self._settings.weekly_report_skill_id}",
            )
        if intent.intent == "query_meeting_rooms":
            return RouteDecision(
                route_type="READ_TOOL",
                target="query_meeting_rooms",
                display_route="只读查询",
            )
        if scene == "refuse_qa":
            return RouteDecision(
                route_type="RAG",
                target="enterprise_knowledge",
                display_route="企业知识-拒答",
            )
        return RouteDecision(
            route_type="RAG",
            target="enterprise_knowledge",
            display_route="企业知识",
        )
