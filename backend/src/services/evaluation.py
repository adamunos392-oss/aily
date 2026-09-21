"""Demo 验证台：只读列出与回放评测案例。不写 meetings / knowledge，不调用 approve。"""

from __future__ import annotations

from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import EvaluationCase as EvaluationCaseRow
from src.models.agent.types import BadCaseCategory, EvaluationCase, SceneId
from src.models.evaluation import (
    EvaluationCaseDetailResponse,
    EvaluationCaseListResponse,
    EvaluationCaseSummary,
    RouteComparison,
)
from src.repositories.evaluation import EvaluationRepository
from src.repositories.mock.evaluation_adapter import EvaluationAdapter

REPLAY_NOTE = "只读回放，不创建会议、不写入企业知识"


class EvaluationCaseNotFoundError(FileNotFoundError):
    """评测案例不存在。"""


class EvaluationService:
    def __init__(
        self,
        db: AsyncSession,
        repo: EvaluationRepository | None = None,
        adapter: EvaluationAdapter | None = None,
    ) -> None:
        self.db = db
        self.repo = repo if repo is not None else EvaluationRepository(db)
        self.adapter = adapter if adapter is not None else EvaluationAdapter()

    async def list_cases(self) -> EvaluationCaseListResponse:
        rows = await self.repo.list_all()
        items = [self._to_summary(row) for row in rows]
        return EvaluationCaseListResponse(items=items, total=len(items))

    async def get_case(self, case_id: str) -> EvaluationCaseDetailResponse:
        row = await self.repo.get_by_case_id(case_id)
        if row is None:
            raise EvaluationCaseNotFoundError("评测案例不存在")
        snapshot = await self.adapter.get_case(case_id)
        traces = snapshot.trace_events if snapshot is not None else []
        case = EvaluationCase(
            case_id=row.case_id,
            name=row.name,
            scene_id=cast(SceneId, row.scene_id),
            query=row.query,
            expected_route=row.expected_route,
            actual_route=row.actual_route,
            passed=bool(row.passed),
            bad_case_category=cast(BadCaseCategory, row.bad_case_category),
            trace_events=traces,
        )
        return EvaluationCaseDetailResponse(
            case=case,
            route_comparison=RouteComparison(
                expected_route=row.expected_route,
                actual_route=row.actual_route,
                passed=bool(row.passed),
            ),
            replay_note=REPLAY_NOTE,
        )

    def _to_summary(self, row: EvaluationCaseRow) -> EvaluationCaseSummary:
        return EvaluationCaseSummary(
            case_id=row.case_id,
            name=row.name,
            expected_route=row.expected_route,
            actual_route=row.actual_route,
            passed=bool(row.passed),
            bad_case_category=cast(BadCaseCategory, row.bad_case_category),
        )
