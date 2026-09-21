"""确认单请求模型。对齐 docs/api-contracts.md API-F003-01/02。"""

from pydantic import BaseModel


class ConfirmationApproveRequest(BaseModel):
    turn_id: str


class ConfirmationCancelRequest(BaseModel):
    turn_id: str
    reason: str | None = None
