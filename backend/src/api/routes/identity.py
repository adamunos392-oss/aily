"""演示身份。API-F001-01 GET /api/identity。"""

from fastapi import Depends
from pycore.api import APIRouter

from src.api.deps import get_current_user
from src.api.envelope import success
from src.models.identity import IdentityResponse
from src.models.user_context import UserContext

router = APIRouter(prefix="/api/identity", tags=["identity"])


@router.get("")
async def get_identity(user: UserContext = Depends(get_current_user)) -> object:
    data = IdentityResponse.from_user(user)
    return success(data.model_dump())
