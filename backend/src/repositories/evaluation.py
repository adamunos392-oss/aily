"""评测案例仓储：只读 evaluation_cases。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import EvaluationCase


class EvaluationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_all(self) -> list[EvaluationCase]:
        stmt = select(EvaluationCase).order_by(EvaluationCase.id.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_case_id(self, case_id: str) -> EvaluationCase | None:
        stmt = select(EvaluationCase).where(EvaluationCase.case_id == case_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
