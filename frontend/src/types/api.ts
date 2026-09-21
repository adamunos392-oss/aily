export interface ApiEnvelope<T> {
  code: number | string;
  message: string;
  data: T | null;
}

export type EntrySource =
  | "manual"
  | "shortcut_knowledge"
  | "shortcut_meeting"
  | "shortcut_report"
  | "shortcut_query"
  | "shortcut_task";

export type TurnStatus =
  | "processing"
  | "replied"
  | "clarifying"
  | "awaiting_confirmation"
  | "unknown"
  | "refused";

export type MessageType =
  | "text"
  | "knowledge_table"
  | "refusal"
  | "clarification"
  | "disambiguation"
  | "confirmation"
  | "meeting_success"
  | "meeting_unknown"
  | "report_draft"
  | "room_list"
  | "empty";

export type IntentName =
  | "enterprise_knowledge"
  | "create_meeting"
  | "generate_work_report"
  | "query_meeting_rooms"
  | "unknown";

export type OperationType = "READ" | "WRITE";

export type RouteType = "RAG" | "SKILL" | "READ_TOOL";

export type ConfirmationStatus = "pending" | "approved" | "cancelled" | "invalidated";

export type TraceNode =
  | "query_rewrite"
  | "intent"
  | "slot_fill"
  | "memory"
  | "risk_permission"
  | "router"
  | "rag_retrieve"
  | "citation_validate"
  | "skill"
  | "tool_call"
  | "confirmation"
  | "result_validate"
  | "final";

export interface IdentityResponse {
  user_id: string;
  display_name: string;
  department: string;
  permissions: Array<"conversation:read" | "conversation:write" | "knowledge:read">;
}

export interface ConversationSummary {
  conversation_id: string;
  title: string;
  updated_at: string;
  preview: string | null;
}

export interface ConversationListResponse {
  items: ConversationSummary[];
  total: number;
}

export interface TurnSummary {
  turn_id: string;
  role: "user" | "assistant";
  content: string;
  status: TurnStatus;
  created_at: string;
}

export interface SlotState {
  slots: Record<string, string | string[] | null>;
  missing_required: string[];
  is_complete: boolean;
}

export interface ConfirmationSummary {
  confirmation_id: string;
  turn_id: string;
  status: ConfirmationStatus;
  meeting_time: string;
  attendees: string[];
  topic: string;
  duration_minutes: number;
  meeting_type: "online" | "offline";
  slot_snapshot_hash: string;
}

export interface ConversationDetailResponse {
  conversation_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  turns: TurnSummary[];
  active_slot_state: SlotState | null;
  active_confirmation: ConfirmationSummary | null;
}

export interface ConversationCreateRequest {
  title: string | null;
}

export interface KnowledgeTableRow {
  level: string;
  city_type: string;
  limit_cny: number;
}

export interface ChoiceOption {
  choice_id: string;
  label: string;
}

export interface ReportDraft {
  draft_id: string;
  skill_name: string;
  content: string;
  is_edited: boolean;
}

export interface MeetingRoomItem {
  room_name: string;
  available_from: string;
  available_to: string;
}

export interface AssistantMessage {
  message_type: MessageType;
  text: string | null;
  table_rows: KnowledgeTableRow[] | null;
  choices: ChoiceOption[] | null;
  confirmation: ConfirmationSummary | null;
  report_draft: ReportDraft | null;
  rooms: MeetingRoomItem[] | null;
}

export interface Citation {
  document_title: string;
  section: string;
  excerpt: string;
  knowledge_entry_id: string;
}

export interface RouteDecision {
  route_type: RouteType;
  target: string;
  display_route: string;
}

export interface TraceEvent {
  event_id: string;
  turn_id: string;
  sequence: number;
  occurred_at: string;
  node: TraceNode;
  title_zh: string;
  summary: string;
  payload: Record<string, unknown>;
}

export interface IntentResult {
  intent: IntentName;
  operation_type: OperationType;
  confidence: number;
}

export interface TurnResponse {
  turn_id: string;
  conversation_id: string;
  status: TurnStatus;
  user_message: string;
  assistant_message: AssistantMessage;
  citations: Citation[];
  route_decision: RouteDecision;
  trace_events: TraceEvent[];
  intent: IntentResult;
  slot_state: SlotState | null;
}

export interface TurnCreateRequest {
  content: string;
  entry_source: EntrySource;
  choice_id: string | null;
  client_turn_key: string | null;
}

export interface ConfirmationApproveRequest {
  turn_id: string;
}

export interface ConfirmationCancelRequest {
  turn_id: string;
  reason: string | null;
}

export interface SlotUpdateRequest {
  updates: Record<string, string>;
}

export interface ReportDraftUpdateRequest {
  content: string;
}

export interface ReportDraftResponse {
  draft_id: string;
  turn_id: string;
  content: string;
  is_edited: boolean;
  updated_at: string;
}

export type DemoSceneId =
  | "empty"
  | "loading"
  | "qa-success"
  | "qa-refuse"
  | "meeting-clarify"
  | "meeting-disambiguate"
  | "meeting-confirm"
  | "meeting-success"
  | "meeting-timeout"
  | "meeting-stale"
  | "report"
  | "rooms"
  | "rooms-empty";

export type EvaluationProtoSceneId = "cases" | "case-timeout" | "cases-empty";

export type BadCaseCategory =
  | "none"
  | "no_evidence_refusal"
  | "timeout_unknown"
  | "confirmation_invalidated";

export type EvaluationSceneId = "S-001" | "S-002" | "S-003" | "S-004" | "S-005" | "S-006" | "S-007";

export interface EvaluationCaseSummary {
  case_id: string;
  name: string;
  expected_route: string;
  actual_route: string;
  passed: boolean;
  bad_case_category: BadCaseCategory;
}

export interface EvaluationCaseListResponse {
  items: EvaluationCaseSummary[];
  total: number;
}

export interface EvaluationCase {
  case_id: string;
  name: string;
  scene_id: EvaluationSceneId;
  query: string;
  expected_route: string;
  actual_route: string;
  passed: boolean;
  bad_case_category: BadCaseCategory;
  trace_events: TraceEvent[];
}

export interface RouteComparison {
  expected_route: string;
  actual_route: string;
  passed: boolean;
}

export interface EvaluationCaseDetailResponse {
  case: EvaluationCase;
  route_comparison: RouteComparison;
  replay_note: string;
}
