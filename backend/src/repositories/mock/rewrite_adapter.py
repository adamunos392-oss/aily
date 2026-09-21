"""Mock Rewrite Adapter。deterministic 改写。"""

from src.core.config import AppSettings, settings
from src.models.agent.types import QueryContext, RewriteResult
from src.repositories.mock.query_rules import classify_scene


class RewriteAdapter:
    def __init__(self, app_settings: AppSettings | None = None) -> None:
        self._settings = app_settings if app_settings is not None else settings

    async def rewrite(self, query: QueryContext) -> RewriteResult:
        scene = classify_scene(query.raw_query, query.entry_source, self._settings)
        rewritten = query.raw_query.strip()
        if scene == "travel_qa":
            rewritten = "差旅住宿标准"
        return RewriteResult(raw_query=query.raw_query, rewritten_query=rewritten)
