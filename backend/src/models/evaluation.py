"""评测案例响应。对齐 docs/api-contracts.md API-F006-01/02。"""

from pydantic import BaseModel

from src.models.agent.types import BadCaseCategory, EvaluationCase


class EvaluationCaseSummary(BaseModel):
    case_id: str
    name: str
    expected_route: str
    actual_route: str
    passed: bool
    bad_case_category: BadCaseCategory


class EvaluationCaseListResponse(BaseModel):
    items: list[EvaluationCaseSummary]
    total: int


class RouteComparison(BaseModel):
    expected_route: str
    actual_route: str
    passed: bool


class EvaluationCaseDetailResponse(BaseModel):
    case: EvaluationCase
    route_comparison: RouteComparison
    replay_note: str
