"""轮次仓储：turns / citations / trace_events。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Citation, ReportDraft, TraceEvent, Turn


class TurnRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, conversation_id: str, turn_id: str) -> Turn | None:
        stmt = select(Turn).where(
            Turn.conversation_id == conversation_id,
            Turn.turn_id == turn_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_client_key(self, conversation_id: str, client_turn_key: str) -> Turn | None:
        stmt = select(Turn).where(
            Turn.conversation_id == conversation_id,
            Turn.client_turn_key == client_turn_key,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_citations(self, turn_id: str) -> list[Citation]:
        stmt = select(Citation).where(Citation.turn_id == turn_id).order_by(Citation.id.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_trace_events(self, turn_id: str) -> list[TraceEvent]:
        stmt = (
            select(TraceEvent)
            .where(TraceEvent.turn_id == turn_id)
            .order_by(TraceEvent.sequence.asc(), TraceEvent.id.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_report_draft(self, turn_id: str, draft_id: str | None = None) -> ReportDraft | None:
        stmt = select(ReportDraft).where(ReportDraft.turn_id == turn_id)
        if draft_id is not None:
            stmt = stmt.where(ReportDraft.draft_id == draft_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
