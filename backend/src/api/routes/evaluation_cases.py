"""评测案例。API-F006-01/02，仅 Demo 验证台消费。"""

from fastapi import Depends
from pycore.api import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_db
from src.api.envelope import failure, success
from src.models.user_context import UserContext
from src.services.evaluation import EvaluationCaseNotFoundError, EvaluationService

router = APIRouter(prefix="/api/evaluation_cases", tags=["evaluation_cases"])


def _service(db: AsyncSession) -> EvaluationService:
    return EvaluationService(db)


@router.get("")
async def list_evaluation_cases(
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> object:
    del user
    data = await _service(db).list_cases()
    return success(data.model_dump(mode="json"))


@router.get("/{case_id}")
async def get_evaluation_case(
    case_id: str,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> object:
    del user
    try:
        data = await _service(db).get_case(case_id)
    except EvaluationCaseNotFoundError:
        return failure(404, "评测案例不存在", "NOT_FOUND")
    return success(data.model_dump(mode="json"))
