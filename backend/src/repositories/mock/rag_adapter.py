"""Mock RAG Adapter。知识召回 + Citation。"""

from src.core.config import AppSettings, settings
from src.models.agent.types import Citation, QueryContext, RagAdapterResult
from src.repositories.mock.query_rules import classify_scene

_TRAVEL_HITS: tuple[tuple[str, str, str, str, float], ...] = (
    (
        "《差旅管理制度（2024 版）》",
        "第 3.2 条 员工住宿标准",
        "职级 P1-P3 在一线城市住宿限额 800 元/晚。",
        "know-travel-p1-tier1",
        0.96,
    ),
    (
        "《差旅管理制度（2024 版）》",
        "第 3.2 条 员工住宿标准",
        "职级 P1-P3 在其他城市住宿限额 600 元/晚。",
        "know-travel-p1-other",
        0.93,
    ),
    (
        "《差旅管理制度（2024 版）》",
        "第 3.2 条 员工住宿标准",
        "职级 P4 及以上在一线城市住宿限额 1200 元/晚。",
        "know-travel-p4-tier1",
        0.91,
    ),
    (
        "《费用报销规范》",
        "第 2.1 条 差旅费用报销要求",
        "差旅住宿以职级与城市类型对照表执行，限额见差旅管理制度。",
        "know-travel-reimburse",
        0.88,
    ),
)


class RagAdapter:
    def __init__(self, app_settings: AppSettings | None = None) -> None:
        self._settings = app_settings if app_settings is not None else settings

    async def retrieve(self, query: QueryContext, rewritten_query: str) -> RagAdapterResult:
        scene = classify_scene(rewritten_query or query.raw_query, query.entry_source, self._settings)
        top_k = self._settings.rag_top_k
        if scene != "travel_qa":
            return RagAdapterResult(hits=[], hit_count=0, scores=[])
        selected = _TRAVEL_HITS[:top_k]
        hits = [
            Citation(
                document_title=title,
                section=section,
                excerpt=excerpt,
                knowledge_entry_id=entry_id,
            )
            for title, section, excerpt, entry_id, _score in selected
        ]
        scores = [score for _title, _section, _excerpt, _entry_id, score in selected]
        return RagAdapterResult(hits=hits, hit_count=len(hits), scores=scores)
