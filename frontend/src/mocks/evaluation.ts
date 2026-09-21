import type {
  ApiEnvelope,
  EvaluationCase,
  EvaluationCaseDetailResponse,
  EvaluationCaseListResponse,
  EvaluationCaseSummary,
  TraceEvent,
  TraceNode,
} from "@/types/api";
import { failEnvelope, okEnvelope } from "@/utils/envelope";

const REPLAY_NOTE = "只读回放，不创建会议、不写入企业知识";

type EvaluationCaseEntity = EvaluationCase;

function event(
  caseId: string,
  turnId: string,
  sequence: number,
  occurredAt: string,
  node: TraceNode,
  titleZh: string,
  summary: string,
  payload: Record<string, unknown> = {},
): TraceEvent {
  return {
    event_id: `evt-${caseId}-${sequence}`,
    turn_id: turnId,
    sequence,
    occurred_at: occurredAt,
    node,
    title_zh: titleZh,
    summary,
    payload: { ...payload },
  };
}

function caseEntity(
  partial: Omit<EvaluationCaseEntity, "actual_route" | "passed" | "trace_events"> & {
    actual_route?: string;
    passed?: boolean;
    trace_events: TraceEvent[];
  },
): EvaluationCaseEntity {
  return {
    case_id: partial.case_id,
    name: partial.name,
    scene_id: partial.scene_id,
    query: partial.query,
    expected_route: partial.expected_route,
    actual_route: partial.actual_route ?? partial.expected_route,
    passed: partial.passed ?? true,
    bad_case_category: partial.bad_case_category,
    trace_events: partial.trace_events,
  };
}

const CASES: EvaluationCaseEntity[] = [
  caseEntity({
    case_id: "eval-qa-travel",
    name: "差旅住宿标准",
    scene_id: "S-001",
    query: "公司的差旅住宿标准是什么？",
    expected_route: "企业知识",
    bad_case_category: "none",
    trace_events: [
      event("eval-qa-travel", "turn-eval-qa-travel", 1, "2026-09-21T02:24:01Z", "query_rewrite", "问题改写", ""),
      event("eval-qa-travel", "turn-eval-qa-travel", 2, "2026-09-21T02:24:02Z", "intent", "意图识别", ""),
      event("eval-qa-travel", "turn-eval-qa-travel", 3, "2026-09-21T02:24:03Z", "router", "路由到企业知识", ""),
      event("eval-qa-travel", "turn-eval-qa-travel", 4, "2026-09-21T02:24:04Z", "rag_retrieve", "知识检索", ""),
      event("eval-qa-travel", "turn-eval-qa-travel", 5, "2026-09-21T02:24:05Z", "citation_validate", "引用核验通过", ""),
      event("eval-qa-travel", "turn-eval-qa-travel", 6, "2026-09-21T02:24:06Z", "final", "最终已回复", ""),
    ],
  }),
  caseEntity({
    case_id: "eval-qa-refuse",
    name: "无依据问句拒答",
    scene_id: "S-002",
    query: "下季度期权行权价是多少？",
    expected_route: "企业知识-拒答",
    bad_case_category: "no_evidence_refusal",
    trace_events: [
      event("eval-qa-refuse", "turn-eval-qa-refuse", 1, "2026-09-21T02:25:01Z", "rag_retrieve", "知识检索未命中", ""),
      event("eval-qa-refuse", "turn-eval-qa-refuse", 2, "2026-09-21T02:25:02Z", "citation_validate", "引用核验未通过", ""),
      event("eval-qa-refuse", "turn-eval-qa-refuse", 3, "2026-09-21T02:25:03Z", "final", "最终已拒答", ""),
    ],
  }),
  caseEntity({
    case_id: "eval-meeting-success",
    name: "创建项目复盘会",
    scene_id: "S-003",
    query: "帮我明天下午三点跟张明开一个项目复盘会。",
    expected_route: "技能 create_meeting",
    bad_case_category: "none",
    trace_events: [
      event("eval-meeting-success", "turn-eval-meeting-success", 1, "2026-09-21T01:49:01Z", "risk_permission", "风险与权限", ""),
      event("eval-meeting-success", "turn-eval-meeting-success", 2, "2026-09-21T01:49:02Z", "confirmation", "确认已同意", ""),
      event("eval-meeting-success", "turn-eval-meeting-success", 3, "2026-09-21T01:49:03Z", "result_validate", "结果核验成功", ""),
    ],
  }),
  caseEntity({
    case_id: "eval-meeting-timeout",
    name: "创建会议超时",
    scene_id: "S-006",
    query: "帮我约明天下午 3 点和张明开项目复盘会",
    expected_route: "技能 create_meeting → 未知",
    bad_case_category: "timeout_unknown",
    trace_events: [
      event("eval-meeting-timeout", "turn-eval-timeout", 1, "2026-09-21T09:00:00Z", "confirmation", "确认已同意", ""),
      event(
        "eval-meeting-timeout",
        "turn-eval-timeout",
        2,
        "2026-09-21T09:00:10Z",
        "tool_call",
        "原子能力超时",
        "超时",
        { tool_id: "meeting_create", status: "timeout" },
      ),
      event(
        "eval-meeting-timeout",
        "turn-eval-timeout",
        3,
        "2026-09-21T09:00:30Z",
        "result_validate",
        "结果核验未知",
        "未知",
        { status: "unknown" },
      ),
      event("eval-meeting-timeout", "turn-eval-timeout", 4, "2026-09-21T09:00:31Z", "final", "最终未知 · 无会议已创建", ""),
    ],
  }),
  caseEntity({
    case_id: "eval-meeting-stale",
    name: "改时间后重确认",
    scene_id: "S-007",
    query: "改成明天下午两点吧。",
    expected_route: "确认作废后重确认",
    bad_case_category: "confirmation_invalidated",
    trace_events: [
      event("eval-meeting-stale", "turn-eval-stale", 1, "2026-09-21T01:50:01Z", "confirmation", "旧确认已作废", ""),
      event("eval-meeting-stale", "turn-eval-stale", 2, "2026-09-21T01:50:02Z", "confirmation", "新确认待确认", ""),
    ],
  }),
  caseEntity({
    case_id: "eval-report",
    name: "生成本周周报",
    scene_id: "S-004",
    query: "帮我生成本周周报。",
    expected_route: "技能 generate_work_report",
    bad_case_category: "none",
    trace_events: [
      event("eval-report", "turn-eval-report", 1, "2026-09-21T01:12:01Z", "tool_call", "取本周消息", ""),
      event("eval-report", "turn-eval-report", 2, "2026-09-21T01:12:02Z", "skill", "过滤闲聊", ""),
      event("eval-report", "turn-eval-report", 3, "2026-09-21T01:12:03Z", "final", "输出可编辑周报", ""),
    ],
  }),
  caseEntity({
    case_id: "eval-rooms",
    name: "查询可用会议室",
    scene_id: "S-005",
    query: "查询明天下午 3 点以后可用的会议室",
    expected_route: "只读查询",
    bad_case_category: "none",
    trace_events: [
      event("eval-rooms", "turn-eval-rooms", 1, "2026-09-21T00:40:01Z", "router", "只读查询", ""),
      event("eval-rooms", "turn-eval-rooms", 2, "2026-09-21T00:40:02Z", "confirmation", "未出现确认", ""),
      event("eval-rooms", "turn-eval-rooms", 3, "2026-09-21T00:40:03Z", "final", "未创建会议", ""),
    ],
  }),
];

function toSummaryDto(entity: EvaluationCaseEntity): EvaluationCaseSummary {
  return {
    case_id: entity.case_id,
    name: entity.name,
    expected_route: entity.expected_route,
    actual_route: entity.actual_route,
    passed: entity.passed,
    bad_case_category: entity.bad_case_category,
  };
}

function toCaseDto(entity: EvaluationCaseEntity): EvaluationCase {
  return {
    case_id: entity.case_id,
    name: entity.name,
    scene_id: entity.scene_id,
    query: entity.query,
    expected_route: entity.expected_route,
    actual_route: entity.actual_route,
    passed: entity.passed,
    bad_case_category: entity.bad_case_category,
    trace_events: entity.trace_events.map((item) => ({
      event_id: item.event_id,
      turn_id: item.turn_id,
      sequence: item.sequence,
      occurred_at: item.occurred_at,
      node: item.node,
      title_zh: item.title_zh,
      summary: item.summary,
      payload: { ...item.payload },
    })),
  };
}

function toDetailDto(entity: EvaluationCaseEntity): EvaluationCaseDetailResponse {
  return {
    case: toCaseDto(entity),
    route_comparison: {
      expected_route: entity.expected_route,
      actual_route: entity.actual_route,
      passed: entity.passed,
    },
    replay_note: REPLAY_NOTE,
  };
}

export function mockListEvaluationCases(): ApiEnvelope<EvaluationCaseListResponse> {
  const items = CASES.map(toSummaryDto);
  return okEnvelope({ items, total: items.length });
}

export function mockGetEvaluationCase(caseId: string): ApiEnvelope<EvaluationCaseDetailResponse> {
  const entity = CASES.find((item) => item.case_id === caseId);
  if (!entity) {
    return failEnvelope(404, "评测案例不存在");
  }
  return okEnvelope(toDetailDto(entity));
}
