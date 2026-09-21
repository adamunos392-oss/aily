"""对话资源。API-F001-02～04：列表、新建、详情。不实现 turns/confirmations 写闭环。"""

from fastapi import Depends, Query
from pycore.api import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_db
from src.api.envelope import failure, success
from src.core.config import settings
from src.models.conversation import ConversationCreateRequest
from src.models.user_context import UserContext
from src.services.conversation import ConversationNotFoundError, ConversationService

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

_LIMIT_MIN = 1
_LIMIT_MAX = 100


def _service(db: AsyncSession) -> ConversationService:
    return ConversationService(db)


@router.get("")
async def list_conversations(
    limit: int | None = Query(default=None),
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> object:
    resolved = settings.conversation_list_limit if limit is None else limit
    if resolved < _LIMIT_MIN or resolved > _LIMIT_MAX:
        return failure(400, "limit 必须在 1 到 100 之间", "VALIDATION_ERROR")
    data = await _service(db).list_conversations(user, resolved)
    return success(data.model_dump())


@router.post("")
async def create_conversation(
    body: ConversationCreateRequest,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> object:
    data = await _service(db).create_conversation(user, body.title)
    return success(data.model_dump())


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> object:
    try:
        data = await _service(db).get_conversation(user, conversation_id)
    except ConversationNotFoundError:
        return failure(404, "对话不存在", "NOT_FOUND")
    return success(data.model_dump())
