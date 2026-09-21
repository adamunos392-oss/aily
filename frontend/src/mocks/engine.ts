import type {
  ApiEnvelope,
  ConfirmationApproveRequest,
  ConfirmationCancelRequest,
  ConversationCreateRequest,
  ConversationDetailResponse,
  ConversationListResponse,
  DemoSceneId,
  EntrySource,
  IdentityResponse,
  ReportDraftResponse,
  SlotUpdateRequest,
  TurnCreateRequest,
  TurnResponse,
  TurnStatus,
} from "@/types/api";
import { failEnvelope, okEnvelope } from "@/utils/envelope";
import {
  TIMEOUT_CONVERSATION_ID,
  availableRooms,
  defaultMeetingConfirmation,
  emptyAssistant,
  knowledgeCitations,
  knowledgeRows,
  makeEvent,
  MOCK_USER_ID,
  ragRoute,
  REFUSE_QUERIES,
  reportDraft,
  roomsRoute,
  skillMeetingRoute,
  skillReportRoute,
  toConfirmationDto,
  toConversationDetailDto,
  toConversationListDto,
  toIdentityDto,
  toReportDraftResponseDto,
  toTurnResponseDto,
  type ConfirmationEntity,
  type ConversationEntity,
  type TurnEntity,
  zhangMingChoices,
} from "@/mocks/dto";

const CONVERSATION_LIST_LIMIT = 20;

interface MockDb {
  conversations: ConversationEntity[];
  turns: TurnEntity[];
  confirmations: ConfirmationEntity[];
  seq: { conv: number; turn: number; conf: number; draft: number };
}

let db: MockDb = emptyDb();

function emptyDb(): MockDb {
  return {
    conversations: [],
    turns: [],
    confirmations: [],
    seq: { conv: 10, turn: 100, conf: 10, draft: 10 },
  };
}

function nextId(kind: "conv" | "turn" | "conf" | "draft"): string {
  db.seq[kind] += 1;
  const n = String(db.seq[kind]).padStart(3, "0");
  if (kind === "conv") return `conv-${n}`;
  if (kind === "turn") return `turn-${n}`;
  if (kind === "conf") return `cfm-${n}`;
  return `draft-${n}`;
}

function listedConversations(): ConversationEntity[] {
  return db.conversations
    .filter((item) => item.user_id === MOCK_USER_ID && item.listed)
    .sort((a, b) => (a.updated_at < b.updated_at ? 1 : -1));
}

function getConversation(id: string): ConversationEntity | undefined {
  return db.conversations.find((item) => item.conversation_id === id && item.user_id === MOCK_USER_ID);
}

function turnsOf(conversationId: string): TurnEntity[] {
  return db.turns.filter((item) => item.conversation_id === conversationId);
}

function confirmationsOf(conversationId: string): ConfirmationEntity[] {
  return db.confirmations.filter((item) => item.conversation_id === conversationId);
}

function replaceTurns(conversationId: string, turns: TurnEntity[]): void {
  db.turns = db.turns.filter((item) => item.conversation_id !== conversationId).concat(turns);
}

function replaceConfirmations(conversationId: string, items: ConfirmationEntity[]): void {
  db.confirmations = db.confirmations.filter((item) => item.conversation_id !== conversationId).concat(items);
}

function upsertConversation(entity: ConversationEntity): void {
  const index = db.conversations.findIndex((item) => item.conversation_id === entity.conversation_id);
  if (index >= 0) db.conversations[index] = entity;
  else db.conversations.push(entity);
}

function touchConversation(conversationId: string, preview: string, title?: string, updatedAt?: string): void {
  const conv = getConversation(conversationId);
  if (!conv) return;
  conv.preview = preview;
  conv.updated_at = updatedAt ?? conv.updated_at;
  if (title) conv.title = title;
}

export function mockGetIdentity(): ApiEnvelope<IdentityResponse> {
  return okEnvelope(toIdentityDto());
}

export function mockListConversations(limit = CONVERSATION_LIST_LIMIT): ApiEnvelope<ConversationListResponse> {
  if (limit < 1 || limit > 100) {
    return failEnvelope(400, "limit 必须在 1 到 100 之间");
  }
  return okEnvelope(toConversationListDto(listedConversations().slice(0, limit)));
}

export function mockCreateConversation(body: ConversationCreateRequest): ApiEnvelope<ConversationDetailResponse> {
  if (body.title !== null && body.title !== undefined && typeof body.title !== "string") {
    return failEnvelope(400, "title 必须是字符串或 null");
  }
  const now = "2026-09-21T07:00:00Z";
  const entity: ConversationEntity = {
    conversation_id: nextId("conv"),
    user_id: MOCK_USER_ID,
    title: body.title?.trim() ? body.title : "新对话",
    preview: null,
    created_at: now,
    updated_at: now,
    listed: true,
  };
  upsertConversation(entity);
  return okEnvelope(toConversationDetailDto(entity, [], []));
}

export function mockGetConversation(conversationId: string): ApiEnvelope<ConversationDetailResponse> {
  const entity = getConversation(conversationId);
  if (!entity) return failEnvelope(404, "对话不存在");
  return okEnvelope(toConversationDetailDto(entity, turnsOf(conversationId), confirmationsOf(conversationId)));
}

export function mockGetTurn(conversationId: string, turnId: string): ApiEnvelope<TurnResponse> {
  const entity = getConversation(conversationId);
  if (!entity) return failEnvelope(404, "轮次不存在");
  const turn = db.turns.find((item) => item.conversation_id === conversationId && item.turn_id === turnId);
  if (!turn) return failEnvelope(404, "轮次不存在");
  return okEnvelope(toTurnResponseDto(turn));
}

function hasTimeSlot(content: string): boolean {
  return /点|下午|上午|明天|今晚|:\d{2}/.test(content);
}

function isRefuseQuery(content: string): boolean {
  return REFUSE_QUERIES.some((item) => content.includes(item.replace("？", "")) || content.includes(item));
}

function classifyTurn(
  conversationId: string,
  content: string,
  entrySource: EntrySource,
  choiceId: string | null,
): DemoSceneId {
  const pending = confirmationsOf(conversationId).find((item) => item.status === "pending");
  if (pending && /改成|改为/.test(content)) return "meeting-stale";
  if (content.includes("差旅")) return "qa-success";
  if (isRefuseQuery(content) || content.includes("期权")) return "qa-refuse";
  if (content.includes("周报")) return "report";
  if (content.includes("会议室") && (conversationId.includes("rooms-empty") || content.includes("无可用"))) {
    return "rooms-empty";
  }
  if (content.includes("会议室")) return "rooms";
  if (entrySource === "shortcut_task" || choiceId) return "meeting-confirm";
  if (/张明|开会|会议/.test(content) && !hasTimeSlot(content)) return "meeting-clarify";
  if (/张明|开会|会议/.test(content)) return "meeting-disambiguate";
  return "qa-refuse";
}

function persistTurn(turn: TurnEntity, confirmation?: ConfirmationEntity): TurnResponse {
  db.turns.push(turn);
  if (confirmation) {
    db.confirmations = db.confirmations.filter(
      (item) => !(item.conversation_id === turn.conversation_id && item.status === "pending"),
    );
    db.confirmations.push(confirmation);
  }
  const conv = getConversation(turn.conversation_id);
  if (conv) {
    conv.preview = turn.user_message;
    conv.updated_at = turn.created_at;
    if (conv.title === "新对话") {
      conv.title = turn.user_message.slice(0, 20);
    }
  }
  return toTurnResponseDto(turn);
}

export function mockCreateTurn(
  conversationId: string,
  body: TurnCreateRequest,
): ApiEnvelope<TurnResponse> {
  const conv = getConversation(conversationId);
  if (!conv) return failEnvelope(404, "对话不存在");
  if (conv.user_id !== MOCK_USER_ID) return failEnvelope(409, "对话不属于当前身份");
  if (!body.content || !body.content.trim()) return failEnvelope(400, "content 不能为空");

  if (body.client_turn_key) {
    const existing = db.turns.find(
      (item) => item.conversation_id === conversationId && item.client_turn_key === body.client_turn_key,
    );
    if (existing) return okEnvelope(toTurnResponseDto(existing));
  }

  const scene = classifyTurn(conversationId, body.content.trim(), body.entry_source, body.choice_id);
  const turnId = nextId("turn");
  const built = buildSceneTurn(scene, {
    turnId,
    conversationId,
    userMessage: body.content.trim(),
    choiceId: body.choice_id,
  });
  return okEnvelope(persistTurn(built.turn, built.confirmation));
}

export function mockApproveConfirmation(
  conversationId: string,
  confirmationId: string,
  body: ConfirmationApproveRequest,
): ApiEnvelope<TurnResponse> {
  const conv = getConversation(conversationId);
  if (!conv) return failEnvelope(404, "确认单不存在");
  const confirmation = db.confirmations.find(
    (item) => item.conversation_id === conversationId && item.confirmation_id === confirmationId,
  );
  if (!confirmation) return failEnvelope(404, "确认单不存在");
  if (confirmation.status !== "pending") return failEnvelope(409, "确认单已失效，请重新确认");
  if (body.turn_id !== confirmation.turn_id) return failEnvelope(400, "turn_id 与确认单不匹配");

  const sourceTurn = db.turns.find((item) => item.turn_id === confirmation.turn_id);
  if (!sourceTurn) return failEnvelope(404, "轮次不存在");

  const timeout = conversationId === TIMEOUT_CONVERSATION_ID;
  const scene: DemoSceneId = timeout ? "meeting-timeout" : "meeting-success";
  confirmation.status = "approved";
  const built = buildSceneTurn(scene, {
    turnId: confirmation.turn_id,
    conversationId,
    userMessage: sourceTurn.user_message,
    confirmationId: confirmation.confirmation_id,
  });
  const index = db.turns.findIndex((item) => item.turn_id === confirmation.turn_id);
  db.turns[index] = built.turn;
  touchConversation(conversationId, sourceTurn.user_message, undefined, built.turn.created_at);
  return okEnvelope(toTurnResponseDto(built.turn));
}

export function mockCancelConfirmation(
  conversationId: string,
  confirmationId: string,
  body: ConfirmationCancelRequest,
): ApiEnvelope<TurnResponse> {
  const confirmation = db.confirmations.find(
    (item) => item.conversation_id === conversationId && item.confirmation_id === confirmationId,
  );
  if (!confirmation) return failEnvelope(404, "确认单不存在");
  if (confirmation.status !== "pending") return failEnvelope(409, "确认单不可取消");
  if (body.turn_id !== confirmation.turn_id) return failEnvelope(400, "turn_id 与确认单不匹配");
  confirmation.status = "cancelled";
  const turn = db.turns.find((item) => item.turn_id === confirmation.turn_id);
  if (!turn) return failEnvelope(404, "轮次不存在");
  turn.status = "replied";
  turn.assistant_message = emptyAssistant({
    message_type: "text",
    text: "已取消创建会议，未创建会议。",
  });
  turn.assistant_message.confirmation = toConfirmationDto(confirmation);
  return okEnvelope(toTurnResponseDto(turn));
}

export function mockUpdateSlots(
  conversationId: string,
  turnId: string,
  body: SlotUpdateRequest,
): ApiEnvelope<TurnResponse> {
  if (!body.updates || Object.keys(body.updates).length === 0) {
    return failEnvelope(400, "updates 不能为空");
  }
  const turn = db.turns.find((item) => item.conversation_id === conversationId && item.turn_id === turnId);
  if (!turn) return failEnvelope(404, "轮次不存在");
  if (turn.intent.intent !== "create_meeting") {
    return failEnvelope(409, "当前轮次不允许修改会议槽位");
  }
  const old = db.confirmations.find(
    (item) => item.conversation_id === conversationId && item.turn_id === turnId && item.status === "pending",
  );
  if (old) old.status = "invalidated";
  const newId = nextId("conf");
  const newTime = body.updates.meeting_time || "明天下午 15:00";
  const built = buildSceneTurn("meeting-stale", {
    turnId,
    conversationId,
    userMessage: turn.user_message,
    confirmationId: newId,
    staleOldTime: old?.meeting_time ?? "14:00",
    newMeetingTime: newTime,
  });
  const index = db.turns.findIndex((item) => item.turn_id === turnId);
  db.turns[index] = built.turn;
  if (built.confirmation) {
    db.confirmations.push(built.confirmation);
  }
  return okEnvelope(toTurnResponseDto(built.turn));
}

export function mockSaveReportDraft(
  conversationId: string,
  turnId: string,
  draftId: string,
  content: string,
): ApiEnvelope<ReportDraftResponse> {
  if (!content) return failEnvelope(400, "content 不能为空");
  const turn = db.turns.find((item) => item.conversation_id === conversationId && item.turn_id === turnId);
  if (!turn || !turn.assistant_message.report_draft || turn.assistant_message.report_draft.draft_id !== draftId) {
    return failEnvelope(404, "周报草稿不存在");
  }
  turn.assistant_message.report_draft.content = content;
  turn.assistant_message.report_draft.is_edited = true;
  const updatedAt = "2026-09-21T08:00:00Z";
  return okEnvelope(toReportDraftResponseDto(turn.assistant_message.report_draft, turnId, updatedAt));
}

interface BuildArgs {
  turnId: string;
  conversationId: string;
  userMessage: string;
  choiceId?: string | null;
  confirmationId?: string;
  staleOldTime?: string;
  newMeetingTime?: string;
}

function buildSceneTurn(scene: DemoSceneId, args: BuildArgs): { turn: TurnEntity; confirmation?: ConfirmationEntity } {
  switch (scene) {
    case "qa-success":
      return { turn: buildQaSuccess(args) };
    case "qa-refuse":
      return { turn: buildQaRefuse(args) };
    case "meeting-clarify":
      return { turn: buildMeetingClarify(args) };
    case "meeting-disambiguate":
      return { turn: buildMeetingDisambiguate(args) };
    case "meeting-confirm":
      return buildMeetingConfirm(args);
    case "meeting-success":
      return { turn: buildMeetingSuccess(args) };
    case "meeting-timeout":
      return { turn: buildMeetingTimeout(args) };
    case "meeting-stale":
      return buildMeetingStale(args);
    case "report":
      return { turn: buildReport(args) };
    case "rooms":
      return { turn: buildRooms(args, false) };
    case "rooms-empty":
      return { turn: buildRooms(args, true) };
    case "loading":
      return { turn: buildLoading(args) };
    default:
      return { turn: buildEmptyTurn(args) };
  }
}

function baseTurn(args: BuildArgs, status: TurnStatus, createdAt: string): Omit<TurnEntity, "assistant_message" | "citations" | "route_decision" | "trace_events" | "intent" | "slot_state"> {
  return {
    turn_id: args.turnId,
    conversation_id: args.conversationId,
    client_turn_key: null,
    created_at: createdAt,
    status,
    user_message: args.userMessage,
  };
}

function buildQaSuccess(args: BuildArgs): TurnEntity {
  const t = "2026-09-21T02:24:03Z";
  return {
    ...baseTurn(args, "replied", t),
    assistant_message: emptyAssistant({
      message_type: "knowledge_table",
      text: "根据企业差旅管理制度，为您查询到住宿标准：\n\n以上标准适用于公司正式员工的商务差旅，实际报销以发票和公司差旅制度为准。",
      table_rows: knowledgeRows(),
    }),
    citations: knowledgeCitations(),
    route_decision: ragRoute(),
    intent: { intent: "enterprise_knowledge", operation_type: "READ", confidence: 1 },
    slot_state: null,
    trace_events: [
      makeEvent(args.turnId, 1, "2026-09-21T02:24:01Z", "query_rewrite", "问题改写", "原始问题：公司的差旅住宿标准是什么？<br/>改写后：查询公司差旅住宿标准 2024", {
        rewritten_query: "查询公司差旅住宿标准 2024",
      }),
      makeEvent(args.turnId, 2, "2026-09-21T02:24:01Z", "intent", "意图识别", "意图：企业制度咨询　只读", {
        intent: "enterprise_knowledge",
        operation_type: "READ",
      }),
      makeEvent(args.turnId, 3, "2026-09-21T02:24:01Z", "router", "路由", "企业知识检索", {
        route_type: "RAG",
        target: "enterprise_knowledge",
      }),
      makeEvent(args.turnId, 4, "2026-09-21T02:24:02Z", "rag_retrieve", "知识检索", "命中 5 条相关文档，选用前 3 条", {
        hit_count: 5,
      }),
      makeEvent(args.turnId, 5, "2026-09-21T02:24:03Z", "citation_validate", "引用核验", "引用数量 2，核验通过", {
        valid: true,
      }),
      makeEvent(args.turnId, 6, "2026-09-21T02:24:03Z", "final", "最终结果", "已回复 · 企业知识问答", {
        status: "replied",
      }),
    ],
  };
}

function buildQaRefuse(args: BuildArgs): TurnEntity {
  const t = "2026-09-21T03:02:03Z";
  return {
    ...baseTurn(args, "refused", t),
    assistant_message: emptyAssistant({
      message_type: "refusal",
      text: "以上内容基于公司内部知识。如有特殊情况请咨询行政部门。",
    }),
    citations: [],
    route_decision: ragRoute(),
    intent: { intent: "enterprise_knowledge", operation_type: "READ", confidence: 1 },
    slot_state: null,
    trace_events: [
      makeEvent(args.turnId, 1, "2026-09-21T03:02:01Z", "query_rewrite", "问题改写", "改写后：查询下季度期权行权价"),
      makeEvent(args.turnId, 2, "2026-09-21T03:02:01Z", "intent", "意图识别", "意图：企业制度咨询　只读", {
        operation_type: "READ",
      }),
      makeEvent(args.turnId, 3, "2026-09-21T03:02:02Z", "router", "路由", "企业知识检索"),
      makeEvent(args.turnId, 4, "2026-09-21T03:02:02Z", "rag_retrieve", "知识检索", "未命中可引用条目", { hit_count: 0 }),
      makeEvent(args.turnId, 5, "2026-09-21T03:02:03Z", "citation_validate", "引用核验", "未通过", { valid: false }),
      makeEvent(args.turnId, 6, "2026-09-21T03:02:03Z", "final", "最终结果", "已拒答", { status: "refused" }),
    ],
  };
}

function buildMeetingClarify(args: BuildArgs): TurnEntity {
  const t = "2026-09-21T01:49:02Z";
  return {
    ...baseTurn(args, "clarifying", t),
    assistant_message: emptyAssistant({
      message_type: "clarification",
      text: "还需要补全会议时间。请问安排在哪一天、几点？",
    }),
    citations: [],
    route_decision: skillMeetingRoute(),
    intent: { intent: "create_meeting", operation_type: "WRITE", confidence: 1 },
    slot_state: {
      slots: { attendees: "张明", meeting_time: null, topic: null },
      missing_required: ["meeting_time", "topic"],
      is_complete: false,
    },
    trace_events: [
      makeEvent(args.turnId, 1, "2026-09-21T01:49:01Z", "intent", "意图识别", "意图：创建会议　写入", {
        operation_type: "WRITE",
      }),
      makeEvent(args.turnId, 2, "2026-09-21T01:49:01Z", "slot_fill", "槽位填充", "已填：参会人张明（未消歧）　缺失：时间、主题"),
      makeEvent(args.turnId, 3, "2026-09-21T01:49:02Z", "final", "最终结果", "待澄清"),
    ],
  };
}

function buildMeetingDisambiguate(args: BuildArgs): TurnEntity {
  const t = "2026-09-21T01:49:02Z";
  return {
    ...baseTurn(args, "clarifying", t),
    assistant_message: emptyAssistant({
      message_type: "disambiguation",
      text: "通讯录里有两位张明，请选择具体的人：",
      choices: zhangMingChoices(),
    }),
    citations: [],
    route_decision: skillMeetingRoute(),
    intent: { intent: "create_meeting", operation_type: "WRITE", confidence: 1 },
    slot_state: {
      slots: { meeting_time: "明天下午 15:00", attendees: "张明", topic: "项目复盘会" },
      missing_required: ["selected_person_id"],
      is_complete: false,
    },
    trace_events: [
      makeEvent(args.turnId, 1, "2026-09-21T01:49:01Z", "intent", "意图识别", "意图：创建会议　写入", {
        operation_type: "WRITE",
      }),
      makeEvent(args.turnId, 2, "2026-09-21T01:49:01Z", "slot_fill", "槽位填充", "时间已填，参会人存在同名"),
      makeEvent(args.turnId, 3, "2026-09-21T01:49:02Z", "skill", "技能", "创建会议 · 等待选定人员"),
      makeEvent(args.turnId, 4, "2026-09-21T01:49:02Z", "final", "最终结果", "待澄清"),
    ],
  };
}

function buildMeetingConfirm(args: BuildArgs): { turn: TurnEntity; confirmation: ConfirmationEntity } {
  const t = "2026-09-21T01:50:02Z";
  const confirmationId = args.confirmationId ?? nextId("conf");
  const confirmation = {
    ...defaultMeetingConfirmation(args.turnId, confirmationId, "pending"),
    conversation_id: args.conversationId,
  };
  const turn: TurnEntity = {
    ...baseTurn(args, "awaiting_confirmation", t),
    assistant_message: emptyAssistant({
      message_type: "confirmation",
      text: "请确认创建会议",
      confirmation: toConfirmationDto(confirmation),
    }),
    citations: [],
    route_decision: skillMeetingRoute(),
    intent: { intent: "create_meeting", operation_type: "WRITE", confidence: 1 },
    slot_state: {
      slots: {
        meeting_time: "明天下午 15:00",
        attendees: ["张明（产品部）", "林小北"],
        topic: "项目复盘会",
        selected_person_id: args.choiceId ?? "person:zhangming-product",
      },
      missing_required: [],
      is_complete: true,
    },
    trace_events: [
      makeEvent(args.turnId, 1, "2026-09-21T01:50:01Z", "risk_permission", "风险与权限", "写入操作 · 当前身份林小北｜产品部"),
      makeEvent(args.turnId, 2, "2026-09-21T01:50:01Z", "skill", "技能", "创建会议 · 编排找人、日历、会议"),
      makeEvent(args.turnId, 3, "2026-09-21T01:50:02Z", "confirmation", "确认", "状态：待确认", { status: "pending" }),
      makeEvent(args.turnId, 4, "2026-09-21T01:50:02Z", "final", "最终结果", "待确认 · 尚未创建"),
    ],
  };
  return { turn, confirmation };
}

function buildMeetingSuccess(args: BuildArgs): TurnEntity {
  const t = "2026-09-21T01:50:04Z";
  const confirmation = defaultMeetingConfirmation(args.turnId, args.confirmationId ?? "cfm-success", "approved");
  return {
    ...baseTurn(args, "replied", t),
    assistant_message: emptyAssistant({
      message_type: "meeting_success",
      text: "会议已创建。\n时间：明天下午 15:00\n参会人：张明（产品部）、林小北\n主题：项目复盘会",
      confirmation,
    }),
    citations: [],
    route_decision: skillMeetingRoute(),
    intent: { intent: "create_meeting", operation_type: "WRITE", confidence: 1 },
    slot_state: {
      slots: { meeting_time: "明天下午 15:00" },
      missing_required: [],
      is_complete: true,
    },
    trace_events: [
      makeEvent(args.turnId, 1, "2026-09-21T01:50:01Z", "risk_permission", "风险与权限", "写入操作"),
      makeEvent(args.turnId, 2, "2026-09-21T01:50:02Z", "confirmation", "确认", "状态：已同意", { status: "approved" }),
      makeEvent(args.turnId, 3, "2026-09-21T01:50:03Z", "tool_call", "原子能力", "找人成功 · 日历可写 · 会议已写入"),
      makeEvent(args.turnId, 4, "2026-09-21T01:50:04Z", "result_validate", "结果核验", "成功", { status: "success" }),
      makeEvent(args.turnId, 5, "2026-09-21T01:50:04Z", "final", "最终结果", "已回复 · 会议已创建", { status: "replied" }),
    ],
  };
}

function buildMeetingTimeout(args: BuildArgs): TurnEntity {
  const t = "2026-09-21T01:51:03Z";
  const confirmation = defaultMeetingConfirmation(args.turnId, args.confirmationId ?? "cfm-timeout", "approved");
  return {
    ...baseTurn(args, "unknown", t),
    assistant_message: emptyAssistant({
      message_type: "meeting_unknown",
      text: "已确认的会议信息仍保留，但系统未在约定等待内得到确定成功。",
      confirmation,
    }),
    citations: [],
    route_decision: skillMeetingRoute(),
    intent: { intent: "create_meeting", operation_type: "WRITE", confidence: 1 },
    slot_state: { slots: { meeting_time: "明天下午 15:00" }, missing_required: [], is_complete: true },
    trace_events: [
      makeEvent(args.turnId, 1, "2026-09-21T01:51:01Z", "confirmation", "确认", "状态：已同意", { status: "approved" }),
      makeEvent(args.turnId, 2, "2026-09-21T01:51:02Z", "tool_call", "原子能力", "创建会议超时", { status: "timeout" }),
      makeEvent(args.turnId, 3, "2026-09-21T01:51:03Z", "result_validate", "结果核验", "未知", { status: "unknown" }),
      makeEvent(args.turnId, 4, "2026-09-21T01:51:03Z", "final", "最终结果", "未知 · 待核验", { status: "unknown" }),
    ],
  };
}

function buildMeetingStale(args: BuildArgs): { turn: TurnEntity; confirmation: ConfirmationEntity } {
  const t = "2026-09-21T01:52:02Z";
  const confirmationId = args.confirmationId ?? nextId("conf");
  const newTime = args.newMeetingTime ?? "明天下午 15:00";
  const confirmation: ConfirmationEntity = {
    ...defaultMeetingConfirmation(args.turnId, confirmationId, "pending"),
    meeting_time: newTime,
    slot_snapshot_hash: "hash-meeting-new",
    conversation_id: args.conversationId,
  };
  const oldTime = args.staleOldTime ?? "14:00";
  const turn: TurnEntity = {
    ...baseTurn(args, "awaiting_confirmation", t),
    user_message: args.userMessage.includes("改成") ? args.userMessage : "改成明天下午两点吧。",
    assistant_message: emptyAssistant({
      message_type: "confirmation",
      text: "请重新确认",
      confirmation: toConfirmationDto(confirmation),
    }),
    citations: [],
    route_decision: skillMeetingRoute(),
    intent: { intent: "create_meeting", operation_type: "WRITE", confidence: 1 },
    slot_state: {
      slots: { meeting_time: newTime, previous_meeting_time: oldTime },
      missing_required: [],
      is_complete: true,
    },
    trace_events: [
      makeEvent(args.turnId, 1, "2026-09-21T01:52:01Z", "slot_fill", "槽位填充", `会议时间由 ${oldTime} 改为 ${newTime}`),
      makeEvent(args.turnId, 2, "2026-09-21T01:52:01Z", "confirmation", "确认", "旧确认已作废", {
        status: "invalidated",
        meeting_time: oldTime,
      }),
      makeEvent(args.turnId, 3, "2026-09-21T01:52:02Z", "confirmation", "确认", "新确认：待确认", { status: "pending" }),
      makeEvent(args.turnId, 4, "2026-09-21T01:52:02Z", "final", "最终结果", "待确认"),
    ],
  };
  return { turn, confirmation };
}

function buildReport(args: BuildArgs): TurnEntity {
  const t = "2026-09-21T01:12:03Z";
  const draftId = nextId("draft");
  return {
    ...baseTurn(args, "replied", t),
    assistant_message: emptyAssistant({
      message_type: "report_draft",
      text: "已命中技能：生成工作周报。按固定步骤生成本周周报，事实来自本轮工作消息。",
      report_draft: reportDraft(draftId),
    }),
    citations: [],
    route_decision: skillReportRoute(),
    intent: { intent: "generate_work_report", operation_type: "READ", confidence: 1 },
    slot_state: null,
    trace_events: [
      makeEvent(args.turnId, 1, "2026-09-21T01:12:01Z", "router", "路由", "技能：生成工作周报"),
      makeEvent(args.turnId, 2, "2026-09-21T01:12:02Z", "skill", "技能", "生成工作周报 · 套用简洁中文事项列表"),
      makeEvent(args.turnId, 3, "2026-09-21T01:12:02Z", "tool_call", "原子能力", "已取本周工作消息"),
      makeEvent(args.turnId, 4, "2026-09-21T01:12:03Z", "final", "最终结果", "已回复 · 可编辑周报"),
    ],
  };
}

function buildRooms(args: BuildArgs, emptyRooms: boolean): TurnEntity {
  const t = emptyRooms ? "2026-09-21T00:41:03Z" : "2026-09-21T00:40:03Z";
  return {
    ...baseTurn(args, "replied", t),
    assistant_message: emptyAssistant({
      message_type: "room_list",
      text: emptyRooms ? "该时段没有可用会议室。" : "明天下午 15:00 以后可用的会议室：",
      rooms: emptyRooms ? [] : availableRooms(),
    }),
    citations: [],
    route_decision: roomsRoute(),
    intent: { intent: "query_meeting_rooms", operation_type: "READ", confidence: 1 },
    slot_state: null,
    trace_events: emptyRooms
      ? [
          makeEvent(args.turnId, 1, "2026-09-21T00:41:01Z", "intent", "意图识别", "意图：查询会议室　只读", {
            operation_type: "READ",
          }),
          makeEvent(args.turnId, 2, "2026-09-21T00:41:02Z", "tool_call", "原子能力", "查询会议室 · 无空闲"),
          makeEvent(args.turnId, 3, "2026-09-21T00:41:03Z", "final", "最终结果", "已回复 · 未预订、未创建会议"),
        ]
      : [
          makeEvent(args.turnId, 1, "2026-09-21T00:40:01Z", "intent", "意图识别", "意图：查询会议室　只读", {
            operation_type: "READ",
          }),
          makeEvent(args.turnId, 2, "2026-09-21T00:40:02Z", "router", "路由", "只读查询"),
          makeEvent(args.turnId, 3, "2026-09-21T00:40:02Z", "tool_call", "原子能力", "查询会议室成功"),
          makeEvent(args.turnId, 4, "2026-09-21T00:40:03Z", "final", "最终结果", "已回复 · 未创建会议"),
        ],
  };
}

function buildLoading(args: BuildArgs): TurnEntity {
  return {
    ...baseTurn(args, "processing", "2026-09-21T02:24:01Z"),
    assistant_message: emptyAssistant({ message_type: "empty", text: "正在处理本轮提问…" }),
    citations: [],
    route_decision: ragRoute(),
    intent: { intent: "enterprise_knowledge", operation_type: "READ", confidence: 1 },
    slot_state: null,
    trace_events: [
      makeEvent(args.turnId, 1, "2026-09-21T02:24:01Z", "query_rewrite", "问题改写", "正在改写当前问题"),
    ],
  };
}

function buildEmptyTurn(args: BuildArgs): TurnEntity {
  return {
    ...baseTurn(args, "replied", "2026-09-21T07:00:00Z"),
    assistant_message: emptyAssistant({ message_type: "empty", text: null }),
    citations: [],
    route_decision: ragRoute(),
    intent: { intent: "unknown", operation_type: "READ", confidence: 1 },
    slot_state: null,
    trace_events: [],
  };
}

function seedConversation(
  id: string,
  title: string,
  preview: string,
  updatedAt: string,
  createdAt: string,
  listed: boolean,
): ConversationEntity {
  const entity: ConversationEntity = {
    conversation_id: id,
    user_id: MOCK_USER_ID,
    title,
    preview,
    created_at: createdAt,
    updated_at: updatedAt,
    listed,
  };
  upsertConversation(entity);
  return entity;
}

function seedFromScene(conversationId: string, scene: DemoSceneId, userMessage: string, listed: boolean, title: string, updatedAt: string): void {
  const existing = getConversation(conversationId);
  seedConversation(
    conversationId,
    existing?.title ?? title,
    existing?.preview ?? userMessage,
    existing?.updated_at ?? updatedAt,
    existing?.created_at ?? updatedAt,
    existing?.listed ?? listed,
  );
  const turnId = `turn-${conversationId}`;
  const built = buildSceneTurn(scene, { turnId, conversationId, userMessage });
  replaceTurns(conversationId, built.turn.status === "processing" ? [] : [built.turn]);
  replaceConfirmations(conversationId, built.confirmation ? [built.confirmation] : []);
}

export function resetMockDb(): void {
  db = emptyDb();
  seedFromScene(
    "conv-001",
    "qa-success",
    "公司的差旅住宿标准是什么？",
    true,
    "差旅住宿标准",
    "2026-09-21T02:24:00Z",
  );
  seedFromScene(
    "conv-002",
    "meeting-confirm",
    "帮我明天下午三点跟张明开一个项目复盘会。",
    true,
    "项目复盘会",
    "2026-09-21T01:49:00Z",
  );
  seedFromScene("conv-003", "report", "帮我生成本周周报。", true, "本周周报", "2026-09-21T01:12:00Z");
  seedFromScene(
    "conv-004",
    "rooms",
    "查询明天下午 3 点以后可用的会议室",
    true,
    "查询会议室",
    "2026-09-21T00:40:00Z",
  );
  const previewById: Record<string, string> = {
    "conv-001": "公司的差旅住宿标准是什么？",
    "conv-002": "帮我明天下午三点跟张明开项目复盘会",
    "conv-003": "帮我生成本周周报",
    "conv-004": "查询明天下午三点以后可用的会议室",
  };
  for (const [id, preview] of Object.entries(previewById)) {
    const conv = getConversation(id);
    if (conv) conv.preview = preview;
  }
  seedConversation(
    TIMEOUT_CONVERSATION_ID,
    "超时演示",
    "帮我明天下午三点跟张明开一个项目复盘会。",
    "2026-09-21T01:51:00Z",
    "2026-09-21T01:51:00Z",
    false,
  );
}

export interface SceneApplyResult {
  conversation: ConversationDetailResponse;
  turn: TurnResponse | null;
  sceneId: DemoSceneId;
  loading: boolean;
  composerText: string;
}

export function mockApplyScene(sceneId: DemoSceneId): ApiEnvelope<SceneApplyResult> {
  const map: Record<DemoSceneId, { convId: string; userMessage: string; composer: string }> = {
    empty: { convId: "conv-empty", userMessage: "", composer: "" },
    loading: { convId: "conv-001", userMessage: "公司的差旅住宿标准是什么？", composer: "公司的差旅住宿标准是什么？" },
    "qa-success": { convId: "conv-001", userMessage: "公司的差旅住宿标准是什么？", composer: "" },
    "qa-refuse": { convId: "conv-001", userMessage: "下季度期权行权价是多少？", composer: "" },
    "meeting-clarify": { convId: "conv-002", userMessage: "帮我跟张明开个会。", composer: "" },
    "meeting-disambiguate": {
      convId: "conv-002",
      userMessage: "帮我明天下午三点跟张明开一个项目复盘会。",
      composer: "",
    },
    "meeting-confirm": {
      convId: "conv-002",
      userMessage: "帮我明天下午三点跟张明开一个项目复盘会。",
      composer: "",
    },
    "meeting-success": {
      convId: "conv-002",
      userMessage: "帮我明天下午三点跟张明开一个项目复盘会。",
      composer: "",
    },
    "meeting-timeout": {
      convId: TIMEOUT_CONVERSATION_ID,
      userMessage: "帮我明天下午三点跟张明开一个项目复盘会。",
      composer: "",
    },
    "meeting-stale": { convId: "conv-002", userMessage: "改成明天下午两点吧。", composer: "" },
    report: { convId: "conv-003", userMessage: "帮我生成本周周报。", composer: "" },
    rooms: { convId: "conv-004", userMessage: "查询明天下午 3 点以后可用的会议室", composer: "" },
    "rooms-empty": { convId: "conv-rooms-empty", userMessage: "查询明天下午 3 点以后可用的会议室", composer: "" },
  };
  const spec = map[sceneId];
  if (sceneId === "empty") {
    const created = mockCreateConversation({ title: null });
    if (created.code !== 200 || !created.data) return failEnvelope(500, "内部错误");
    created.data.title = "新对话";
    return okEnvelope({
      conversation: created.data,
      turn: null,
      sceneId,
      loading: false,
      composerText: "",
    });
  }
  const listed = spec.convId !== TIMEOUT_CONVERSATION_ID && spec.convId !== "conv-rooms-empty";
  seedFromScene(spec.convId, sceneId, spec.userMessage, listed, getConversation(spec.convId)?.title ?? spec.userMessage.slice(0, 12), getConversation(spec.convId)?.updated_at ?? "2026-09-21T02:24:00Z");
  if (sceneId === "loading") {
    const conv = getConversation(spec.convId)!;
    replaceTurns(spec.convId, []);
    return okEnvelope({
      conversation: toConversationDetailDto(conv, [], []),
      turn: toTurnResponseDto(
        buildLoading({ turnId: "turn-loading", conversationId: spec.convId, userMessage: spec.userMessage }),
      ),
      sceneId,
      loading: true,
      composerText: spec.composer,
    });
  }
  const conv = getConversation(spec.convId)!;
  const turns = turnsOf(spec.convId);
  const last = turns[turns.length - 1] ?? null;
  return okEnvelope({
    conversation: toConversationDetailDto(conv, turns, confirmationsOf(spec.convId)),
    turn: last ? toTurnResponseDto(last) : null,
    sceneId,
    loading: false,
    composerText: spec.composer,
  });
}

resetMockDb();
