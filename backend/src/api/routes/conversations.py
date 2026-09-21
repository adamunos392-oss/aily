"""对话资源。API-F001-02～04 与 API-F002-01/02 turns。"""

from fastapi import Depends, Query
from pycore.api import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_db
from src.api.envelope import failure, success
from src.core.config import settings
from src.models.conversation import ConversationCreateRequest
from src.models.report import ReportDraftUpdateRequest
from src.models.turn import SlotUpdateRequest, TurnCreateRequest
from src.models.user_context import UserContext
from src.services.confirmation import (
    ConfirmationService,
    EmptySlotUpdatesError,
    SlotUpdateNotAllowedError,
)
from src.services.conversation import ConversationNotFoundError, ConversationService
from src.services.report import EmptyReportContentError, ReportDraftNotFoundError, ReportService
from src.services.turn import (
    ConversationForbiddenError,
    EmptyTurnContentError,
    TurnNotFoundError,
    TurnService,
)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

_LIMIT_MIN = 1
_LIMIT_MAX = 100


def _service(db: AsyncSession) -> ConversationService:
    return ConversationService(db)


def _turn_service(db: AsyncSession) -> TurnService:
    return TurnService(db)


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


@router.post("/{conversation_id}/turns")
async def create_turn(
    conversation_id: str,
    body: TurnCreateRequest,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> object:
    try:
        data = await _turn_service(db).create_turn(
            user,
            conversation_id,
            content=body.content,
            entry_source=body.entry_source,
            choice_id=body.choice_id,
            client_turn_key=body.client_turn_key,
        )
    except EmptyTurnContentError:
        return failure(400, "content 不能为空", "VALIDATION_ERROR")
    except ConversationNotFoundError:
        return failure(404, "对话不存在", "NOT_FOUND")
    except ConversationForbiddenError:
        return failure(409, "对话不属于当前身份", "CONFLICT")
    return success(data.model_dump(mode="json"))


@router.get("/{conversation_id}/turns/{turn_id}")
async def get_turn(
    conversation_id: str,
    turn_id: str,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> object:
    try:
        data = await _turn_service(db).get_turn(user, conversation_id, turn_id)
    except ConversationNotFoundError:
        return failure(404, "轮次不存在", "NOT_FOUND")
    except ConversationForbiddenError:
        return failure(404, "轮次不存在", "NOT_FOUND")
    except TurnNotFoundError:
        return failure(404, "轮次不存在", "NOT_FOUND")
    return success(data.model_dump(mode="json"))


@router.patch("/{conversation_id}/turns/{turn_id}/slots")
async def update_turn_slots(
    conversation_id: str,
    turn_id: str,
    body: SlotUpdateRequest,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> object:
    try:
        data = await ConfirmationService(db).update_slots(
            user, conversation_id, turn_id, body.updates
        )
    except EmptySlotUpdatesError:
        return failure(400, "updates 不能为空", "VALIDATION_ERROR")
    except (TurnNotFoundError, ConversationNotFoundError):
        return failure(404, "轮次不存在", "NOT_FOUND")
    except ConversationForbiddenError:
        return failure(409, "对话不属于当前身份", "CONFLICT")
    except SlotUpdateNotAllowedError:
        return failure(409, "当前轮次不允许修改会议槽位", "CONFLICT")
    return success(data.model_dump(mode="json"))


@router.patch("/{conversation_id}/turns/{turn_id}/report_drafts/{draft_id}")
async def update_report_draft(
    conversation_id: str,
    turn_id: str,
    draft_id: str,
    body: ReportDraftUpdateRequest,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> object:
    try:
        data = await ReportService(db).update_draft(
            user, conversation_id, turn_id, draft_id, body.content
        )
    except EmptyReportContentError:
        return failure(400, "content 不能为空", "VALIDATION_ERROR")
    except ConversationNotFoundError:
        return failure(404, "对话不存在", "NOT_FOUND")
    except ConversationForbiddenError:
        return failure(409, "对话不属于当前身份", "CONFLICT")
    except TurnNotFoundError:
        return failure(404, "轮次不存在", "NOT_FOUND")
    except ReportDraftNotFoundError:
        return failure(404, "周报草稿不存在", "NOT_FOUND")
    return success(data.model_dump())
