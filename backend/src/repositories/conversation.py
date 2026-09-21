"""对话仓储：所有查询必须带 user_id 过滤。"""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Confirmation, Conversation, Turn


class ConversationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_user(self, user_id: str, limit: int) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_user(self, user_id: str) -> int:
        stmt = select(func.count()).select_from(Conversation).where(Conversation.user_id == user_id)
        result = await self.db.execute(stmt)
        return int(result.scalar_one())

    async def get_by_id_for_user(self, conversation_id: str, user_id: str) -> Conversation | None:
        stmt = select(Conversation).where(
            Conversation.conversation_id == conversation_id,
            Conversation.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        conversation_id: str,
        user_id: str,
        title: str,
        created_at: str,
        updated_at: str,
    ) -> Conversation:
        row = Conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            title=title,
            preview=None,
            created_at=created_at,
            updated_at=updated_at,
        )
        self.db.add(row)
        try:
            await self.db.flush()
        except IntegrityError as exc:
            await self.db.rollback()
            raise ValueError("对话创建冲突") from exc
        await self.db.refresh(row)
        return row

    async def list_turns(self, conversation_id: str) -> list[Turn]:
        stmt = (
            select(Turn)
            .where(Turn.conversation_id == conversation_id)
            .order_by(Turn.created_at.asc(), Turn.id.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_confirmation(self, conversation_id: str) -> Confirmation | None:
        stmt = select(Confirmation).where(
            Confirmation.conversation_id == conversation_id,
            Confirmation.status == "pending",
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
