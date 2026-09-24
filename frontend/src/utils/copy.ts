import type { BadCaseCategory, RouteType, TraceEvent, TraceNode } from "@/types/api";

export const DEMO_SCENE_OPTIONS: Array<{ id: string; label: string }> = [
  { id: "empty", label: "空对话" },
  { id: "loading", label: "发送中" },
  { id: "qa-success", label: "知识有据" },
  { id: "qa-refuse", label: "知识拒答" },
  { id: "meeting-clarify", label: "会议缺槽澄清" },
  { id: "meeting-disambiguate", label: "同名消歧" },
  { id: "meeting-confirm", label: "会议待确认" },
  { id: "meeting-success", label: "会议已创建" },
  { id: "meeting-timeout", label: "会议超时未知" },
  { id: "meeting-stale", label: "确认作废重确认" },
  { id: "report", label: "周报可编辑" },
  { id: "rooms", label: "会议室有结果" },
  { id: "rooms-empty", label: "会议室无可用" },
];

export const SHORTCUTS: Array<{
  id: string;
  title: string;
  subtitle: string;
  query: string;
  entrySource:
    | "shortcut_knowledge"
    | "shortcut_meeting"
    | "shortcut_report"
    | "shortcut_query"
    | "shortcut_task";
}> = [
  {
    id: "knowledge",
    title: "知识问答",
    subtitle: "查询企业知识",
    query: "公司的差旅住宿标准是什么？",
    entrySource: "shortcut_knowledge",
  },
  {
    id: "meeting",
    title: "创建会议",
    subtitle: "安排日程会议",
    query: "帮我明天下午三点跟张明开一个项目复盘会。",
    entrySource: "shortcut_meeting",
  },
  {
    id: "report",
    title: "生成周报",
    subtitle: "一键生成周报",
    query: "帮我生成本周周报",
    entrySource: "shortcut_report",
  },
  {
    id: "query",
    title: "查询信息",
    subtitle: "查询可用会议室",
    query: "查询明天下午 3 点以后可用的会议室",
    entrySource: "shortcut_query",
  },
  {
    id: "task",
    title: "执行任务",
    subtitle: "创建会议",
    query: "帮我明天下午三点跟张明开一个项目复盘会。",
    entrySource: "shortcut_task",
  },
];

export const EVALUATION_SCENE_OPTIONS: Array<{ id: string; label: string }> = [
  { id: "cases", label: "案例列表" },
  { id: "case-timeout", label: "选中超时案例" },
  { id: "cases-empty", label: "列表空" },
];

const BAD_CASE_LABELS: Record<BadCaseCategory, string> = {
  none: "无",
  no_evidence_refusal: "无依据拒答",
  timeout_unknown: "超时未知",
  confirmation_invalidated: "确认失效",
};

export function evaluationBadCaseLabel(category: BadCaseCategory): string {
  return BAD_CASE_LABELS[category];
}

export function evaluationRouteLabel(route: string): string {
  if (route === "技能 create_meeting") return "创建会议技能";
  if (route === "技能 create_meeting → 未知") return "创建会议技能 → 未知";
  if (route === "技能 generate_work_report") return "生成工作周报技能";
  return route;
}

export type ConversationSceneTag = "RAG" | "Skill" | "Tool";

export function conversationSceneTag(
  preview: string | null,
  title: string,
  routeType: RouteType | null,
): ConversationSceneTag | null {
  if (routeType === "RAG") return "RAG";
  if (routeType === "SKILL") return "Skill";
  if (routeType === "READ_TOOL") return "Tool";
  const text = `${preview ?? ""} ${title}`;
  if (text.includes("会议室")) return "Tool";
  if (text.includes("周报") || text.includes("开会") || text.includes("会议")) return "Skill";
  if (text.includes("差旅") || text.includes("上市") || text.includes("期权")) return "RAG";
  return null;
}

export type TraceKindTag =
  | "RAG"
  | "INTENT"
  | "SLOT"
  | "SKILL"
  | "CHECK"
  | "CONFIRM"
  | "TOOL"
  | "VERIFY"
  | "READ"
  | "WRITE"
  | "SUCCESS"
  | "UNKNOWN";

const NODE_TAGS: Partial<Record<TraceNode, TraceKindTag>> = {
  query_rewrite: "RAG",
  intent: "INTENT",
  slot_fill: "SLOT",
  risk_permission: "CHECK",
  rag_retrieve: "RAG",
  citation_validate: "RAG",
  skill: "SKILL",
  confirmation: "CONFIRM",
  result_validate: "VERIFY",
};

export function traceKindTag(event: TraceEvent): TraceKindTag | null {
  const fromNode = NODE_TAGS[event.node];
  if (fromNode) return fromNode;
  if (event.node === "result_validate" || event.node === "final") {
    const blob = `${event.summary} ${event.title_zh} ${JSON.stringify(event.payload)}`;
    if (blob.includes("未知")) return "UNKNOWN";
    if (blob.includes("成功") || blob.includes("已回复") || blob.includes("已创建")) return "SUCCESS";
    if (event.node === "result_validate") return "VERIFY";
    return null;
  }
  if (event.node === "tool_call") {
    return "TOOL";
  }
  if (event.node === "router") {
    const target = String(event.payload.target ?? event.payload.route_type ?? "");
    if (target.includes("RAG") || event.summary.includes("知识")) return "RAG";
    if (target.includes("SKILL") || event.summary.includes("技能")) return "SKILL";
    return "TOOL";
  }
  if (event.summary.endsWith("\u3000写入")) return "WRITE";
  if (event.summary.endsWith("\u3000只读")) return "READ";
  return null;
}

export function traceStatusLabel(event: TraceEvent): string {
  const status = event.payload.status;
  if (typeof status === "string" && status.trim()) {
    if (status === "pending") return "待确认";
    if (status === "approved") return "已同意";
    if (status === "invalidated") return "已作废";
    if (status === "cancelled") return "已取消";
    if (status === "success") return "成功";
    if (status === "unknown" || status === "timeout") return "未知";
    if (status === "refused") return "拒答";
    return status;
  }
  if (event.node === "final") return event.title_zh.replace(/^最终/, "") || "完成";
  return "已执行";
}

export function nextDemoMeetingTime(current: string): string {
  if (current.includes("14:00") || current.includes("两点")) return "明天下午三点";
  return "明天下午两点";
}
