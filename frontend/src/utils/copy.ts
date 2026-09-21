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
