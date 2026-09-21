"""Mock 演示身份上下文。字段对齐 docs/api-contracts.md IdentityResponse。"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

MockPermission = Literal["conversation:read", "conversation:write", "knowledge:read"]

MOCK_USER_PERMISSIONS: tuple[MockPermission, ...] = (
    "conversation:read",
    "conversation:write",
    "knowledge:read",
)


class UserContext(BaseModel):
    """路由级注入的 Mock UserContext。无登录 / JWT。"""

    model_config = ConfigDict(frozen=True)

    user_id: str
    display_name: str
    department: str
    permissions: list[MockPermission]
