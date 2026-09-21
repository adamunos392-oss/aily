"""周报草稿请求/响应。对齐 docs/api-contracts.md API-F004-01。"""

from pydantic import BaseModel, field_validator


class ReportDraftUpdateRequest(BaseModel):
    """PATCH report_drafts 请求体。"""

    content: str

    @field_validator("content")
    @classmethod
    def content_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content 不能为空")
        return value


class ReportDraftResponse(BaseModel):
    """PATCH report_drafts 成功体。"""

    draft_id: str
    turn_id: str
    content: str
    is_edited: bool
    updated_at: str
