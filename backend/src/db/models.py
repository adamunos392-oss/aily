"""数据库模型。基于 pycore/integrations/db/models.py 模板扩展，字段对照 docs/data-model.md。"""

from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, Integer, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now_iso() -> str:
    """UTC ISO-8601 文本：YYYY-MM-DDTHH:MM:SSZ。"""
    return datetime.now(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类。"""


class Conversation(Base):
    """对话。"""

    __tablename__ = "conversations"
    __table_args__ = (
        Index("ux_conversations_conversation_id", "conversation_id", unique=True),
        Index("ix_conversations_user_updated", "user_id", "updated_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="新对话")
    preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=utc_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, default=utc_now_iso)


class Turn(Base):
    """一轮提问（单行同时保存用户句与助手结果）。"""

    __tablename__ = "turns"
    __table_args__ = (
        Index("ux_turns_turn_id", "turn_id", unique=True),
        Index("ix_turns_conversation_created", "conversation_id", "created_at"),
        Index(
            "ux_turns_conv_client_key",
            "conversation_id",
            "client_turn_key",
            unique=True,
            sqlite_where=text("client_turn_key IS NOT NULL"),
        ),
        CheckConstraint("role IN ('user', 'assistant')", name="ck_turns_role"),
        CheckConstraint(
            "status IN ('processing', 'replied', 'clarifying', "
            "'awaiting_confirmation', 'unknown', 'refused')",
            name="ck_turns_status",
        ),
        CheckConstraint(
            "entry_source IN ('manual', 'shortcut_knowledge', 'shortcut_meeting', "
            "'shortcut_report', 'shortcut_query', 'shortcut_task')",
            name="ck_turns_entry_source",
        ),
        CheckConstraint(
            "operation_type IS NULL OR operation_type IN ('READ', 'WRITE')",
            name="ck_turns_operation_type",
        ),
        CheckConstraint(
            "route_type IS NULL OR route_type IN ('RAG', 'SKILL', 'READ_TOOL')",
            name="ck_turns_route_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    turn_id: Mapped[str] = mapped_column(Text, nullable=False)
    conversation_id: Mapped[str] = mapped_column(
        Text, ForeignKey("conversations.conversation_id"), nullable=False
    )
    client_turn_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    entry_source: Mapped[str] = mapped_column(Text, nullable=False, default="manual")
    status: Mapped[str] = mapped_column(Text, nullable=False, default="processing")
    intent: Mapped[str | None] = mapped_column(Text, nullable=True)
    operation_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    route_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    route_target: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_route: Mapped[str | None] = mapped_column(Text, nullable=True)
    assistant_message_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    assistant_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    slot_state_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    memory_state_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    choice_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=utc_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, default=utc_now_iso)


class KnowledgeEntry(Base):
    """企业知识条目。"""

    __tablename__ = "knowledge_entries"
    __table_args__ = (
        Index("ux_knowledge_entry_id", "knowledge_entry_id", unique=True),
        CheckConstraint("is_active IN (0, 1)", name="ck_knowledge_is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    knowledge_entry_id: Mapped[str] = mapped_column(Text, nullable=False)
    document_title: Mapped[str] = mapped_column(Text, nullable=False)
    section: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    city_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    level: Mapped[str | None] = mapped_column(Text, nullable=True)
    limit_cny: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Citation(Base):
    """回答引用。"""

    __tablename__ = "citations"
    __table_args__ = (Index("ix_citations_turn", "turn_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    turn_id: Mapped[str] = mapped_column(Text, ForeignKey("turns.turn_id"), nullable=False)
    knowledge_entry_id: Mapped[str] = mapped_column(
        Text, ForeignKey("knowledge_entries.knowledge_entry_id"), nullable=False
    )
    document_title: Mapped[str] = mapped_column(Text, nullable=False)
    section: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=utc_now_iso)


class Confirmation(Base):
    """会议确认单。"""

    __tablename__ = "confirmations"
    __table_args__ = (
        Index("ux_confirmations_confirmation_id", "confirmation_id", unique=True),
        Index("ix_confirmations_conv_status", "conversation_id", "status"),
        Index(
            "ux_confirmations_pending_conversation",
            "conversation_id",
            unique=True,
            sqlite_where=text("status = 'pending'"),
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'cancelled', 'invalidated')",
            name="ck_confirmations_status",
        ),
        CheckConstraint(
            "meeting_type IN ('online', 'offline')",
            name="ck_confirmations_meeting_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    confirmation_id: Mapped[str] = mapped_column(Text, nullable=False)
    conversation_id: Mapped[str] = mapped_column(
        Text, ForeignKey("conversations.conversation_id"), nullable=False
    )
    turn_id: Mapped[str] = mapped_column(Text, ForeignKey("turns.turn_id"), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    meeting_time: Mapped[str] = mapped_column(Text, nullable=False)
    attendees_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    meeting_type: Mapped[str] = mapped_column(Text, nullable=False)
    slot_snapshot_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=utc_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, default=utc_now_iso)


class TraceEvent(Base):
    """事件流节点。"""

    __tablename__ = "trace_events"
    __table_args__ = (
        Index("ux_trace_events_event_id", "event_id", unique=True),
        Index("ux_trace_turn_seq", "turn_id", "sequence", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(Text, nullable=False)
    turn_id: Mapped[str] = mapped_column(Text, ForeignKey("turns.turn_id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    occurred_at: Mapped[str] = mapped_column(Text, nullable=False, default=utc_now_iso)
    node: Mapped[str] = mapped_column(Text, nullable=False)
    title_zh: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")


class ReportDraft(Base):
    """周报草稿。"""

    __tablename__ = "report_drafts"
    __table_args__ = (
        Index("ux_report_drafts_draft_id", "draft_id", unique=True),
        Index("ux_report_drafts_turn_id", "turn_id", unique=True),
        CheckConstraint("is_edited IN (0, 1)", name="ck_report_drafts_is_edited"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draft_id: Mapped[str] = mapped_column(Text, nullable=False)
    turn_id: Mapped[str] = mapped_column(Text, ForeignKey("turns.turn_id"), nullable=False)
    skill_name: Mapped[str] = mapped_column(Text, nullable=False, default="生成工作周报")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_edited: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=utc_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, default=utc_now_iso)


class WorkMessage(Base):
    """本周工作消息。"""

    __tablename__ = "work_messages"
    __table_args__ = (
        Index("ux_work_messages_message_id", "message_id", unique=True),
        CheckConstraint("kind IN ('work', 'chitchat')", name="ck_work_messages_kind"),
        CheckConstraint("is_this_week IN (0, 1)", name="ck_work_messages_is_this_week"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_this_week: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Person(Base):
    """通讯录人员。"""

    __tablename__ = "people"
    __table_args__ = (Index("ux_people_person_id", "person_id", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    department: Mapped[str] = mapped_column(Text, nullable=False)
    job_title: Mapped[str | None] = mapped_column(Text, nullable=True)


class MeetingRoom(Base):
    """会议室。"""

    __tablename__ = "meeting_rooms"
    __table_args__ = (Index("ux_meeting_rooms_room_id", "room_id", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[str] = mapped_column(Text, nullable=False)
    room_name: Mapped[str] = mapped_column(Text, nullable=False)
    available_from: Mapped[str] = mapped_column(Text, nullable=False)
    available_to: Mapped[str] = mapped_column(Text, nullable=False)
    tomorrow_after_hour: Mapped[int] = mapped_column(Integer, nullable=False)


class Meeting(Base):
    """已创建会议结果。超时/取消/作废路径不得插入。"""

    __tablename__ = "meetings"
    __table_args__ = (Index("ux_meetings_meeting_id", "meeting_id", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meeting_id: Mapped[str] = mapped_column(Text, nullable=False)
    conversation_id: Mapped[str] = mapped_column(
        Text, ForeignKey("conversations.conversation_id"), nullable=False
    )
    confirmation_id: Mapped[str] = mapped_column(
        Text, ForeignKey("confirmations.confirmation_id"), nullable=False
    )
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    meeting_time: Mapped[str] = mapped_column(Text, nullable=False)
    attendees_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=utc_now_iso)


class EvaluationCase(Base):
    """Demo 验证台预置案例。"""

    __tablename__ = "evaluation_cases"
    __table_args__ = (
        Index("ux_eval_case_id", "case_id", unique=True),
        CheckConstraint(
            "scene_id IN ('S-001', 'S-002', 'S-003', 'S-004', 'S-005', 'S-006', 'S-007')",
            name="ck_evaluation_scene_id",
        ),
        CheckConstraint("passed IN (0, 1)", name="ck_evaluation_passed"),
        CheckConstraint(
            "bad_case_category IN ('none', 'no_evidence_refusal', "
            "'timeout_unknown', 'confirmation_invalidated')",
            name="ck_evaluation_bad_case_category",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    scene_id: Mapped[str] = mapped_column(Text, nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    expected_route: Mapped[str] = mapped_column(Text, nullable=False)
    actual_route: Mapped[str] = mapped_column(Text, nullable=False)
    passed: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    bad_case_category: Mapped[str] = mapped_column(Text, nullable=False, default="none")
    replay_turn_id: Mapped[str | None] = mapped_column(Text, nullable=True)
