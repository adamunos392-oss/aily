"""Mock Intent Adapter。意图 + operation_type，confidence 固定 1.0。"""

from src.core.config import AppSettings, settings
from src.models.agent.types import IntentResult, QueryContext
from src.repositories.mock.query_rules import classify_scene, intent_for_scene

_MOCK_CONFIDENCE = 1.0


class IntentAdapter:
    def __init__(self, app_settings: AppSettings | None = None) -> None:
        self._settings = app_settings if app_settings is not None else settings

    async def classify(self, query: QueryContext, rewritten_query: str) -> IntentResult:
        text = rewritten_query or query.raw_query
        scene = classify_scene(text, query.entry_source, self._settings)
        intent, operation_type = intent_for_scene(scene)
        return IntentResult(
            intent=intent,
            operation_type=operation_type,
            confidence=_MOCK_CONFIDENCE,
        )
