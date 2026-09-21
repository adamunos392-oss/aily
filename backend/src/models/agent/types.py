"""Agent 共享领域类型。字段对齐 docs/tech-spec.md §3.0 / §3.13 与 docs/api-contracts.md。"""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

EntrySource = Literal[
    "manual",
    "shortcut_knowledge",
    "shortcut_meeting",
    "shortcut_report",
    "shortcut_query",
    "shortcut_task",
]
IntentName = Literal[
    "enterprise_knowledge",
    "create_meeting",
    "generate_work_report",
    "query_meeting_rooms",
    "unknown",
]
OperationType = Literal["READ", "WRITE"]
RouteType = Literal["RAG", "SKILL", "READ_TOOL"]
TurnStatus = Literal[
    "processing",
    "replied",
    "clarifying",
    "awaiting_confirmation",
    "unknown",
    "refused",
]
MessageType = Literal[
    "text",
    "knowledge_table",
    "refusal",
    "clarification",
    "disambiguation",
    "confirmation",
    "meeting_success",
    "meeting_unknown",
    "report_draft",
    "room_list",
    "empty",
]
TraceNode = Literal[
    "query_rewrite",
    "intent",
    "slot_fill",
    "memory",
    "risk_permission",
    "router",
    "rag_retrieve",
    "citation_validate",
    "skill",
    "tool_call",
    "confirmation",
    "result_validate",
    "final",
]
ConfirmationStatus = Literal["pending", "approved", "cancelled", "invalidated"]
MeetingType = Literal["online", "offline"]
ToolId = Literal[
    "people_lookup",
    "calendar_check",
    "meeting_create",
    "work_message_fetch",
    "meeting_room_query",
]
SkillId = Literal["create_meeting", "generate_work_report"]
ToolResultStatus = Literal["success", "failure", "timeout", "unknown"]
SceneId = Literal["S-001", "S-002", "S-003", "S-004", "S-005", "S-006", "S-007"]
BadCaseCategory = Literal[
    "none",
    "no_evidence_refusal",
    "timeout_unknown",
    "confirmation_invalidated",
]
MemoryTemplateStyle = Literal["bullet_list"]
MemoryLanguage = Literal["zh-CN"]
MemoryLength = Literal["concise"]

SlotValue = str | list[str] | None


def to_iso_z(moment: datetime) -> str:
    """UTC ISO-8601：YYYY-MM-DDTHH:MM:SSZ。"""
    utc = moment.astimezone(UTC).replace(microsecond=0)
    return utc.strftime("%Y-%m-%dT%H:%M:%SZ")


class QueryContext(BaseModel):
    conversation_id: str
    turn_id: str
    raw_query: str
    entry_source: EntrySource
    user_id: str


class RewriteResult(BaseModel):
    raw_query: str
    rewritten_query: str


class IntentResult(BaseModel):
    intent: IntentName
    operation_type: OperationType
    confidence: float = 1.0


class SlotState(BaseModel):
    slots: dict[str, SlotValue]
    missing_required: list[str]
    is_complete: bool


class MemoryState(BaseModel):
    template_style: MemoryTemplateStyle = "bullet_list"
    language: MemoryLanguage = "zh-CN"
    length: MemoryLength = "concise"


class RouteDecision(BaseModel):
    route_type: RouteType
    target: str
    display_route: str


class Citation(BaseModel):
    document_title: str
    section: str
    excerpt: str
    knowledge_entry_id: str


class ToolDefinition(BaseModel):
    tool_id: ToolId
    name: str
    operation_type: OperationType


class ToolCall(BaseModel):
    tool_id: str
    arguments: dict[str, str | int | list[str]]
    call_id: str


class ToolResult(BaseModel):
    call_id: str
    tool_id: str
    status: ToolResultStatus
    payload: dict[str, Any] | None
    error_message: str | None


class SkillDefinition(BaseModel):
    skill_id: SkillId
    name: str
    description: str
    orchestrated_tools: list[str]


class TraceEvent(BaseModel):
    event_id: str
    turn_id: str
    sequence: int
    occurred_at: datetime
    node: TraceNode
    title_zh: str
    summary: str
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_serializer("occurred_at")
    def serialize_occurred_at(self, value: datetime) -> str:
        return to_iso_z(value)


class EvaluationCase(BaseModel):
    case_id: str
    name: str
    scene_id: SceneId
    query: str
    expected_route: str
    actual_route: str
    passed: bool
    bad_case_category: BadCaseCategory
    trace_events: list[TraceEvent]


class ConfirmationSummary(BaseModel):
    confirmation_id: str
    turn_id: str
    status: ConfirmationStatus
    meeting_time: str
    attendees: list[str]
    topic: str
    duration_minutes: int
    meeting_type: MeetingType
    slot_snapshot_hash: str


class ChoiceOption(BaseModel):
    choice_id: str
    label: str


class ReportDraft(BaseModel):
    draft_id: str
    skill_name: str
    content: str
    is_edited: bool


class MeetingRoomItem(BaseModel):
    room_name: str
    available_from: str
    available_to: str


class KnowledgeTableRow(BaseModel):
    level: str
    city_type: str
    limit_cny: int


class AssistantMessage(BaseModel):
    message_type: MessageType
    text: str | None = None
    table_rows: list[KnowledgeTableRow] | None = None
    choices: list[ChoiceOption] | None = None
    confirmation: ConfirmationSummary | None = None
    report_draft: ReportDraft | None = None
    rooms: list[MeetingRoomItem] | None = None


class ConversationRuntimeState(BaseModel):
    slot_state: SlotState | None = None
    active_confirmation: ConfirmationSummary | None = None
    choice_id: str | None = None
    execute_write: bool = False


class TurnResponse(BaseModel):
    turn_id: str
    conversation_id: str
    status: TurnStatus
    user_message: str
    assistant_message: AssistantMessage
    citations: list[Citation]
    route_decision: RouteDecision
    trace_events: list[TraceEvent]
    intent: IntentResult
    slot_state: SlotState | None


class RagAdapterResult(BaseModel):
    hits: list[Citation]
    hit_count: int
    scores: list[float] = Field(default_factory=list)


class SlotAdapterResult(BaseModel):
    slot_state: SlotState
    key_slot_changed: bool = False
    needs_disambiguation: bool = False
    choices: list[ChoiceOption] = Field(default_factory=list)


class SkillAdapterResult(BaseModel):
    skill_id: str
    status: TurnStatus
    tool_calls: list[ToolCall] = Field(default_factory=list)
    confirmation: ConfirmationSummary | None = None
    choices: list[ChoiceOption] | None = None
    report_draft: ReportDraft | None = None
    message_type: MessageType = "text"
    text: str | None = None


class RiskPermissionResult(BaseModel):
    allowed: bool
    operation_type: OperationType
    summary: str


class ResultValidationOutcome(BaseModel):
    status: TurnStatus
    assistant_message: AssistantMessage
    citations: list[Citation] = Field(default_factory=list)
    citation_valid: bool | None = None
    result_status: Literal["success", "unknown", "refused", "pending"] = "success"


class OrchestratorState(BaseModel):
    """固定链路在各 Plugin 之间传递的可变状态。"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    query: QueryContext
    conversation_state: ConversationRuntimeState = Field(default_factory=ConversationRuntimeState)
    rewrite: RewriteResult | None = None
    intent: IntentResult | None = None
    slot_result: SlotAdapterResult | None = None
    memory_state: MemoryState | None = None
    risk: RiskPermissionResult | None = None
    route: RouteDecision | None = None
    rag: RagAdapterResult | None = None
    skill: SkillAdapterResult | None = None
    tool_results: list[ToolResult] = Field(default_factory=list)
    validation: ResultValidationOutcome | None = None
    trace_events: list[TraceEvent] = Field(default_factory=list)
    sequence: int = 0
