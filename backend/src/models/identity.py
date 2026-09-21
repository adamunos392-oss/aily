"""Identity API 响应模型。对齐 docs/api-contracts.md API-F001-01。"""

from pydantic import BaseModel, ConfigDict

from src.models.user_context import MockPermission, UserContext


class IdentityResponse(BaseModel):
    """GET /api/identity 的 data。"""

    model_config = ConfigDict(frozen=True)

    user_id: str
    display_name: str
    department: str
    permissions: list[MockPermission]

    @classmethod
    def from_user(cls, user: UserContext) -> "IdentityResponse":
        return cls(
            user_id=user.user_id,
            display_name=user.display_name,
            department=user.department,
            permissions=list(user.permissions),
        )


__all__ = ["IdentityResponse"]
