import type {
  AssistantMessage,
  ChoiceOption,
  Citation,
  ConfirmationSummary,
  ConversationDetailResponse,
  ConversationListResponse,
  ConversationSummary,
  IdentityResponse,
  IntentResult,
  KnowledgeTableRow,
  MeetingRoomItem,
  ReportDraft,
  ReportDraftResponse,
  RouteDecision,
  SlotState,
  TraceEvent,
  TraceNode,
  TurnResponse,
  TurnStatus,
  TurnSummary,
} from "@/types/api";

export const MOCK_USER_ID = "mock-linxiaobei";
export const TIMEOUT_CONVERSATION_ID = "conv-demo-meeting-timeout";
export const REFUSE_QUERIES = ["下季度期权行权价是多少？", "公司上市时间表是什么？"];

export interface TurnEntity {
  turn_id: string;
  conversation_id: string;
  client_turn_key: string | null;
  created_at: string;
  status: TurnStatus;
  user_message: string;
  assistant_message: AssistantMessage;
  citations: Citation[];
  route_decision: RouteDecision;
  trace_events: TraceEvent[];
  intent: IntentResult;
  slot_state: SlotState | null;
}

export interface ConversationEntity {
  conversation_id: string;
  user_id: string;
  title: string;
  preview: string | null;
  created_at: string;
  updated_at: string;
  listed: boolean;
}

export interface ConfirmationEntity extends ConfirmationSummary {
  conversation_id: string;
}

export function emptyAssistant(partial: Partial<AssistantMessage> & Pick<AssistantMessage, "message_type">): AssistantMessage {
  return {
    message_type: partial.message_type,
    text: partial.text ?? null,
    table_rows: partial.table_rows ?? null,
    choices: partial.choices ?? null,
    confirmation: partial.confirmation ?? null,
    report_draft: partial.report_draft ?? null,
    rooms: partial.rooms ?? null,
  };
}

export function toIdentityDto(): IdentityResponse {
  return {
    user_id: MOCK_USER_ID,
    display_name: "林小北",
    department: "产品部",
    permissions: ["conversation:read", "conversation:write", "knowledge:read"],
  };
}

export function toConversationSummaryDto(entity: ConversationEntity): ConversationSummary {
  return {
    conversation_id: entity.conversation_id,
    title: entity.title,
    updated_at: entity.updated_at,
    preview: entity.preview,
  };
}

export function toConversationListDto(items: ConversationEntity[]): ConversationListResponse {
  const mapped = items.map(toConversationSummaryDto);
  return { items: mapped, total: mapped.length };
}

function assistantSummaryContent(message: AssistantMessage): string {
  if (message.text) return message.text;
  if (message.report_draft) return message.report_draft.content;
  if (message.confirmation) return "请确认创建会议";
  return "";
}

export function toTurnSummaries(turn: TurnEntity): TurnSummary[] {
  const user: TurnSummary = {
    turn_id: turn.turn_id,
    role: "user",
    content: turn.user_message,
    status: turn.status,
    created_at: turn.created_at,
  };
  if (turn.status === "processing") {
    return [user];
  }
  const assistant: TurnSummary = {
    turn_id: turn.turn_id,
    role: "assistant",
    content: assistantSummaryContent(turn.assistant_message),
    status: turn.status,
    created_at: turn.created_at,
  };
  return [user, assistant];
}

export function toConversationDetailDto(
  entity: ConversationEntity,
  turns: TurnEntity[],
  confirmations: ConfirmationEntity[],
): ConversationDetailResponse {
  const lastTurn = turns[turns.length - 1] ?? null;
  const pending = confirmations.find((item) => item.status === "pending") ?? null;
  return {
    conversation_id: entity.conversation_id,
    title: entity.title,
    created_at: entity.created_at,
    updated_at: entity.updated_at,
    turns: turns.flatMap(toTurnSummaries),
    active_slot_state: lastTurn?.slot_state ?? null,
    active_confirmation: pending
      ? toConfirmationDto(pending)
      : null,
  };
}

export function toConfirmationDto(entity: ConfirmationEntity): ConfirmationSummary {
  return {
    confirmation_id: entity.confirmation_id,
    turn_id: entity.turn_id,
    status: entity.status,
    meeting_time: entity.meeting_time,
    attendees: [...entity.attendees],
    topic: entity.topic,
    duration_minutes: entity.duration_minutes,
    meeting_type: entity.meeting_type,
    slot_snapshot_hash: entity.slot_snapshot_hash,
  };
}

export function toTurnResponseDto(entity: TurnEntity): TurnResponse {
  return {
    turn_id: entity.turn_id,
    conversation_id: entity.conversation_id,
    status: entity.status,
    user_message: entity.user_message,
    assistant_message: {
      message_type: entity.assistant_message.message_type,
      text: entity.assistant_message.text,
      table_rows: entity.assistant_message.table_rows
        ? entity.assistant_message.table_rows.map((row: KnowledgeTableRow) => ({
            level: row.level,
            city_type: row.city_type,
            limit_cny: row.limit_cny,
          }))
        : null,
      choices: entity.assistant_message.choices
        ? entity.assistant_message.choices.map((choice: ChoiceOption) => ({
            choice_id: choice.choice_id,
            label: choice.label,
          }))
        : null,
      confirmation: entity.assistant_message.confirmation
        ? {
            confirmation_id: entity.assistant_message.confirmation.confirmation_id,
            turn_id: entity.assistant_message.confirmation.turn_id,
            status: entity.assistant_message.confirmation.status,
            meeting_time: entity.assistant_message.confirmation.meeting_time,
            attendees: [...entity.assistant_message.confirmation.attendees],
            topic: entity.assistant_message.confirmation.topic,
            duration_minutes: entity.assistant_message.confirmation.duration_minutes,
            meeting_type: entity.assistant_message.confirmation.meeting_type,
            slot_snapshot_hash: entity.assistant_message.confirmation.slot_snapshot_hash,
          }
        : null,
      report_draft: entity.assistant_message.report_draft
        ? {
            draft_id: entity.assistant_message.report_draft.draft_id,
            skill_name: entity.assistant_message.report_draft.skill_name,
            content: entity.assistant_message.report_draft.content,
            is_edited: entity.assistant_message.report_draft.is_edited,
          }
        : null,
      rooms: entity.assistant_message.rooms
        ? entity.assistant_message.rooms.map((room: MeetingRoomItem) => ({
            room_name: room.room_name,
            available_from: room.available_from,
            available_to: room.available_to,
          }))
        : null,
    },
    citations: entity.citations.map((item) => ({
      document_title: item.document_title,
      section: item.section,
      excerpt: item.excerpt,
      knowledge_entry_id: item.knowledge_entry_id,
    })),
    route_decision: {
      route_type: entity.route_decision.route_type,
      target: entity.route_decision.target,
      display_route: entity.route_decision.display_route,
    },
    trace_events: entity.trace_events.map((event) => ({
      event_id: event.event_id,
      turn_id: event.turn_id,
      sequence: event.sequence,
      occurred_at: event.occurred_at,
      node: event.node,
      title_zh: event.title_zh,
      summary: event.summary,
      payload: { ...event.payload },
    })),
    intent: {
      intent: entity.intent.intent,
      operation_type: entity.intent.operation_type,
      confidence: entity.intent.confidence,
    },
    slot_state: entity.slot_state
      ? {
          slots: { ...entity.slot_state.slots },
          missing_required: [...entity.slot_state.missing_required],
          is_complete: entity.slot_state.is_complete,
        }
      : null,
  };
}

export function toReportDraftResponseDto(draft: ReportDraft, turnId: string, updatedAt: string): ReportDraftResponse {
  return {
    draft_id: draft.draft_id,
    turn_id: turnId,
    content: draft.content,
    is_edited: true,
    updated_at: updatedAt,
  };
}

export function makeEvent(
  turnId: string,
  sequence: number,
  occurredAt: string,
  node: TraceNode,
  titleZh: string,
  summary: string,
  payload: Record<string, unknown> = {},
): TraceEvent {
  return {
    event_id: `evt-${turnId}-${sequence}`,
    turn_id: turnId,
    sequence,
    occurred_at: occurredAt,
    node,
    title_zh: titleZh,
    summary,
    payload,
  };
}

export function knowledgeRows(): KnowledgeTableRow[] {
  return [
    { level: "P1-P3", city_type: "一线城市", limit_cny: 800 },
    { level: "P1-P3", city_type: "其他城市", limit_cny: 600 },
    { level: "P4 及以上", city_type: "一线城市", limit_cny: 1200 },
  ];
}

export function knowledgeCitations(): Citation[] {
  return [
    {
      document_title: "《差旅管理制度（2024 版）》",
      section: "第 3.2 条 员工住宿标准",
      excerpt: "一线城市 P1-P3 住宿标准不超过 800 元/晚。",
      knowledge_entry_id: "know-travel-p1-tier1",
    },
    {
      document_title: "《费用报销规范》",
      section: "第 2.1 条 差旅费用报销要求",
      excerpt: "差旅住宿以职级与城市类型对照表执行。",
      knowledge_entry_id: "know-travel-reimburse",
    },
  ];
}

export function zhangMingChoices(): ChoiceOption[] {
  return [
    { choice_id: "person:zhangming-product", label: "张明 · 产品部" },
    { choice_id: "person:zhangming-finance", label: "张明 · 财务部" },
  ];
}

export function availableRooms(): MeetingRoomItem[] {
  return [
    {
      room_name: "星河 3 号",
      available_from: "2026-09-22T07:00:00Z",
      available_to: "2026-09-22T10:00:00Z",
    },
    {
      room_name: "启航厅",
      available_from: "2026-09-22T07:00:00Z",
      available_to: "2026-09-22T08:30:00Z",
    },
  ];
}

export function defaultMeetingConfirmation(turnId: string, confirmationId: string, status: ConfirmationSummary["status"] = "pending"): ConfirmationSummary {
  return {
    confirmation_id: confirmationId,
    turn_id: turnId,
    status,
    meeting_time: "明天下午 15:00",
    attendees: ["张明（产品部）", "林小北"],
    topic: "项目复盘会",
    duration_minutes: 60,
    meeting_type: "online",
    slot_snapshot_hash: "hash-meeting-1500",
  };
}

export function reportDraft(draftId: string, content?: string, isEdited = false): ReportDraft {
  return {
    draft_id: draftId,
    skill_name: "生成工作周报",
    content:
      content ??
      "本周工作周报（林小北）\n1. 完成 Aily 工作台信息架构评审\n2. 与张明对齐项目复盘会材料",
    is_edited: isEdited,
  };
}

export function ragRoute(): RouteDecision {
  return { route_type: "RAG", target: "enterprise_knowledge", display_route: "企业知识" };
}

export function skillMeetingRoute(): RouteDecision {
  return { route_type: "SKILL", target: "create_meeting", display_route: "技能 create_meeting" };
}

export function skillReportRoute(): RouteDecision {
  return { route_type: "SKILL", target: "generate_work_report", display_route: "技能 generate_work_report" };
}

export function roomsRoute(): RouteDecision {
  return { route_type: "READ_TOOL", target: "query_meeting_rooms", display_route: "只读查询" };
}
