"""Mock Evaluation Adapter。预置 EvaluationCase 与对照结果。"""

from datetime import UTC, datetime

from src.core.config import AppSettings, settings
from src.models.agent.types import EvaluationCase, TraceEvent, TraceNode


def _event(
    case_id: str,
    turn_id: str,
    sequence: int,
    occurred_at: datetime,
    node: TraceNode,
    title_zh: str,
    summary: str,
    payload: dict[str, object] | None = None,
) -> TraceEvent:
    return TraceEvent(
        event_id=f"evt-{case_id}-{sequence}",
        turn_id=turn_id,
        sequence=sequence,
        occurred_at=occurred_at,
        node=node,
        title_zh=title_zh,
        summary=summary,
        payload=dict(payload) if payload is not None else {},
    )


class EvaluationAdapter:
    def __init__(self, app_settings: AppSettings | None = None) -> None:
        self._settings = app_settings if app_settings is not None else settings

    async def list_cases(self) -> list[EvaluationCase]:
        cases = self._cases()
        expected = self._settings.evaluation_case_count_expected
        if len(cases) != expected:
            raise ValueError("评测案例条数必须等于 EVALUATION_CASE_COUNT_EXPECTED")
        return cases

    async def get_case(self, case_id: str) -> EvaluationCase | None:
        for item in await self.list_cases():
            if item.case_id == case_id:
                return item
        return None

    def _cases(self) -> list[EvaluationCase]:
        refuse_query = self._settings.knowledge_refuse_demo_query
        create_skill = self._settings.create_meeting_skill_id
        report_skill = self._settings.weekly_report_skill_id
        t1 = datetime(2026, 9, 21, 2, 24, 1, tzinfo=UTC)
        t2 = datetime(2026, 9, 21, 2, 25, 1, tzinfo=UTC)
        t3 = datetime(2026, 9, 21, 1, 49, 1, tzinfo=UTC)
        t4 = datetime(2026, 9, 21, 9, 0, 0, tzinfo=UTC)
        t5 = datetime(2026, 9, 21, 1, 50, 1, tzinfo=UTC)
        t6 = datetime(2026, 9, 21, 1, 12, 1, tzinfo=UTC)
        t7 = datetime(2026, 9, 21, 0, 40, 1, tzinfo=UTC)
        return [
            EvaluationCase(
                case_id="eval-qa-travel",
                name="差旅住宿标准",
                scene_id="S-001",
                query="公司的差旅住宿标准是什么？",
                expected_route="企业知识",
                actual_route="企业知识",
                passed=True,
                bad_case_category="none",
                trace_events=[
                    _event("eval-qa-travel", "turn-eval-qa-travel", 1, t1, "query_rewrite", "问题改写", ""),
                    _event("eval-qa-travel", "turn-eval-qa-travel", 2, t1, "intent", "意图识别", ""),
                    _event("eval-qa-travel", "turn-eval-qa-travel", 3, t1, "router", "路由到企业知识", ""),
                    _event("eval-qa-travel", "turn-eval-qa-travel", 4, t1, "rag_retrieve", "知识检索", ""),
                    _event("eval-qa-travel", "turn-eval-qa-travel", 5, t1, "citation_validate", "引用核验通过", ""),
                    _event("eval-qa-travel", "turn-eval-qa-travel", 6, t1, "final", "最终已回复", ""),
                ],
            ),
            EvaluationCase(
                case_id="eval-qa-refuse",
                name="无依据问句拒答",
                scene_id="S-002",
                query=refuse_query,
                expected_route="企业知识-拒答",
                actual_route="企业知识-拒答",
                passed=True,
                bad_case_category="no_evidence_refusal",
                trace_events=[
                    _event("eval-qa-refuse", "turn-eval-qa-refuse", 1, t2, "rag_retrieve", "知识检索未命中", ""),
                    _event("eval-qa-refuse", "turn-eval-qa-refuse", 2, t2, "citation_validate", "引用核验未通过", ""),
                    _event("eval-qa-refuse", "turn-eval-qa-refuse", 3, t2, "final", "最终已拒答", ""),
                ],
            ),
            EvaluationCase(
                case_id="eval-meeting-success",
                name="创建项目复盘会",
                scene_id="S-003",
                query="帮我明天下午三点跟张明开一个项目复盘会。",
                expected_route=f"技能 {create_skill}",
                actual_route=f"技能 {create_skill}",
                passed=True,
                bad_case_category="none",
                trace_events=[
                    _event("eval-meeting-success", "turn-eval-meeting-success", 1, t3, "risk_permission", "风险与权限", ""),
                    _event("eval-meeting-success", "turn-eval-meeting-success", 2, t3, "confirmation", "确认已同意", ""),
                    _event("eval-meeting-success", "turn-eval-meeting-success", 3, t3, "result_validate", "结果核验成功", ""),
                ],
            ),
            EvaluationCase(
                case_id="eval-meeting-timeout",
                name="创建会议超时",
                scene_id="S-006",
                query="帮我约明天下午 3 点和张明开项目复盘会",
                expected_route=f"技能 {create_skill} → 未知",
                actual_route=f"技能 {create_skill} → 未知",
                passed=True,
                bad_case_category="timeout_unknown",
                trace_events=[
                    _event("eval-meeting-timeout", "turn-eval-timeout", 1, t4, "confirmation", "确认已同意", ""),
                    _event(
                        "eval-meeting-timeout",
                        "turn-eval-timeout",
                        2,
                        t4,
                        "tool_call",
                        "原子能力超时",
                        "超时",
                        {"tool_id": "meeting_create", "status": "timeout"},
                    ),
                    _event(
                        "eval-meeting-timeout",
                        "turn-eval-timeout",
                        3,
                        t4,
                        "result_validate",
                        "结果核验未知",
                        "未知",
                        {"status": "unknown"},
                    ),
                    _event("eval-meeting-timeout", "turn-eval-timeout", 4, t4, "final", "最终未知 · 无会议已创建", ""),
                ],
            ),
            EvaluationCase(
                case_id="eval-meeting-stale",
                name="改时间后重确认",
                scene_id="S-007",
                query="改成明天下午两点吧。",
                expected_route="确认作废后重确认",
                actual_route="确认作废后重确认",
                passed=True,
                bad_case_category="confirmation_invalidated",
                trace_events=[
                    _event("eval-meeting-stale", "turn-eval-stale", 1, t5, "confirmation", "旧确认已作废", ""),
                    _event("eval-meeting-stale", "turn-eval-stale", 2, t5, "confirmation", "新确认待确认", ""),
                ],
            ),
            EvaluationCase(
                case_id="eval-report",
                name="生成本周周报",
                scene_id="S-004",
                query="帮我生成本周周报。",
                expected_route=f"技能 {report_skill}",
                actual_route=f"技能 {report_skill}",
                passed=True,
                bad_case_category="none",
                trace_events=[
                    _event("eval-report", "turn-eval-report", 1, t6, "tool_call", "取本周消息", ""),
                    _event("eval-report", "turn-eval-report", 2, t6, "skill", "过滤闲聊", ""),
                    _event("eval-report", "turn-eval-report", 3, t6, "final", "输出可编辑周报", ""),
                ],
            ),
            EvaluationCase(
                case_id="eval-rooms",
                name="查询可用会议室",
                scene_id="S-005",
                query="查询明天下午 3 点以后可用的会议室",
                expected_route="只读查询",
                actual_route="只读查询",
                passed=True,
                bad_case_category="none",
                trace_events=[
                    _event("eval-rooms", "turn-eval-rooms", 1, t7, "router", "只读查询", ""),
                    _event("eval-rooms", "turn-eval-rooms", 2, t7, "result_validate", "未出现确认", ""),
                    _event("eval-rooms", "turn-eval-rooms", 3, t7, "final", "未创建会议", ""),
                ],
            ),
        ]
