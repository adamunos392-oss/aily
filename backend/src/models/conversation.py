"""对话 API 请求/响应模型。对齐 docs/api-contracts.md API-F001-02～04。"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.models.agent.types import ConfirmationSummary, SlotState, TurnStatus


class ConversationCreateRequest(BaseModel):
    """POST /api/conversations 请求体。"""

    title: str | None = None

    @field_validator("title", mode="before")
    @classmethod
    def title_must_be_str_or_none(cls, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("title 必须是字符串或 null")
        return value


class ConversationSummary(BaseModel):
    """最近对话列表项。"""

    model_config = ConfigDict(from_attributes=True)

    conversation_id: str
    title: str
    updated_at: str
    preview: str | None = None


class ConversationListResponse(BaseModel):
    """GET /api/conversations 的 data。"""

    items: list[ConversationSummary]
    total: int


class TurnSummary(BaseModel):
    """对话详情中的轮次摘要。"""

    turn_id: str
    role: str
    content: str
    status: TurnStatus
    created_at: str


class ConversationDetailResponse(BaseModel):
    """新建/详情 data。切换对话时槽位与确认单只属于该 conversation_id。"""

    conversation_id: str
    title: str
    created_at: str
    updated_at: str
    turns: list[TurnSummary] = Field(default_factory=list)
    active_slot_state: SlotState | None = None
    active_confirmation: ConfirmationSummary | None = None
