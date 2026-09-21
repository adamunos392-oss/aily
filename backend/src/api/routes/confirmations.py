"""确认单同意/取消。API-F003-01/02。"""

from fastapi import Depends
from pycore.api import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_db
from src.api.envelope import failure, success
from src.models.confirmation import ConfirmationApproveRequest, ConfirmationCancelRequest
from src.models.user_context import UserContext
from src.services.confirmation import (
    ConfirmationConflictError,
    ConfirmationNotFoundError,
    ConfirmationService,
    TurnIdMismatchError,
)
from src.services.conversation import ConversationNotFoundError
from src.services.turn import ConversationForbiddenError, TurnNotFoundError

router = APIRouter(prefix="/api/conversations", tags=["confirmations"])


def _service(db: AsyncSession) -> ConfirmationService:
    return ConfirmationService(db)


@router.post("/{conversation_id}/confirmations/{confirmation_id}/approve")
async def approve_confirmation(
    conversation_id: str,
    confirmation_id: str,
    body: ConfirmationApproveRequest,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> object:
    try:
        data = await _service(db).approve(user, conversation_id, confirmation_id, body.turn_id)
    except (ConfirmationNotFoundError, ConversationNotFoundError, TurnNotFoundError):
        return failure(404, "确认单不存在", "NOT_FOUND")
    except ConversationForbiddenError:
        return failure(409, "对话不属于当前身份", "CONFLICT")
    except ConfirmationConflictError:
        return failure(409, "确认单已失效，请重新确认", "CONFLICT")
    except TurnIdMismatchError:
        return failure(400, "turn_id 与确认单不匹配", "VALIDATION_ERROR")
    return success(data.model_dump(mode="json"))


@router.post("/{conversation_id}/confirmations/{confirmation_id}/cancel")
async def cancel_confirmation(
    conversation_id: str,
    confirmation_id: str,
    body: ConfirmationCancelRequest,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> object:
    try:
        data = await _service(db).cancel(user, conversation_id, confirmation_id, body.turn_id)
    except (ConfirmationNotFoundError, ConversationNotFoundError, TurnNotFoundError):
        return failure(404, "确认单不存在", "NOT_FOUND")
    except ConversationForbiddenError:
        return failure(409, "对话不属于当前身份", "CONFLICT")
    except ConfirmationConflictError:
        return failure(409, "确认单不可取消", "CONFLICT")
    except TurnIdMismatchError:
        return failure(400, "turn_id 与确认单不匹配", "VALIDATION_ERROR")
    return success(data.model_dump(mode="json"))
