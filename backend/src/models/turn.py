"""一轮提问请求模型。对齐 docs/api-contracts.md API-F002-01。"""

from pydantic import BaseModel, field_validator

from src.models.agent.types import EntrySource


class TurnCreateRequest(BaseModel):
    """POST /api/conversations/{conversation_id}/turns 请求体。"""

    content: str
    entry_source: EntrySource = "manual"
    choice_id: str | None = None
    client_turn_key: str | None = None

    @field_validator("content")
    @classmethod
    def content_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content 不能为空")
        return value


class SlotUpdateRequest(BaseModel):
    """PATCH /api/conversations/{id}/turns/{turn_id}/slots 请求体。"""

    updates: dict[str, str]

    @field_validator("updates")
    @classmethod
    def updates_must_not_be_empty(cls, value: dict[str, str]) -> dict[str, str]:
        if not value:
            raise ValueError("updates 不能为空")
        return value
