"""幂等种子数据。预置知识 / 人员 / 会议室 / 工作消息 / 评测案例 / 超时演示对话。"""

from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from pycore.core import get_logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import AppSettings, settings
from src.db.models import (
    Base,
    Conversation,
    EvaluationCase,
    KnowledgeEntry,
    MeetingRoom,
    Person,
    WorkMessage,
    utc_now_iso,
)

_SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
_FINANCE_DEPARTMENT = "财务部"
_ROOM_XINGHE_DURATION_MINUTES = 180
_ROOM_QIHANG_DURATION_MINUTES = 90


def format_utc_z(moment: datetime) -> str:
    """将带时区时间格式化为 YYYY-MM-DDTHH:MM:SSZ。"""
    utc = moment.astimezone(UTC).replace(microsecond=0)
    return utc.strftime("%Y-%m-%dT%H:%M:%SZ")


async def _upsert(
    session: AsyncSession,
    model: type[Base],
    key_attr: str,
    key_value: str,
    values: dict[str, Any],
) -> None:
    column = getattr(model, key_attr)
    existing = (await session.execute(select(model).where(column == key_value))).scalar_one_or_none()
    if existing is None:
        payload: dict[str, Any] = {key_attr: key_value, **values}
        session.add(model(**payload))
        return
    for field, value in values.items():
        setattr(existing, field, value)


def _demo_room_window(after_hour: int, offset_days: int, duration_minutes: int) -> tuple[str, str]:
    now_local = datetime.now(_SHANGHAI_TZ)
    day = (now_local + timedelta(days=offset_days)).date()
    start = datetime(day.year, day.month, day.day, after_hour, 0, 0, tzinfo=_SHANGHAI_TZ)
    end = start + timedelta(minutes=duration_minutes)
    return format_utc_z(start), format_utc_z(end)


async def _seed_knowledge(session: AsyncSession) -> None:
    rows: list[dict[str, Any]] = [
        {
            "knowledge_entry_id": "know-travel-p1-tier1",
            "document_title": "《差旅管理制度（2024 版）》",
            "section": "第 3.2 条 员工住宿标准",
            "excerpt": "职级 P1-P3 在一线城市住宿限额 800 元/晚。",
            "city_type": "一线城市",
            "level": "P1-P3",
            "limit_cny": 800,
            "is_active": 1,
        },
        {
            "knowledge_entry_id": "know-travel-p1-other",
            "document_title": "《差旅管理制度（2024 版）》",
            "section": "第 3.2 条 员工住宿标准",
            "excerpt": "职级 P1-P3 在其他城市住宿限额 600 元/晚。",
            "city_type": "其他城市",
            "level": "P1-P3",
            "limit_cny": 600,
            "is_active": 1,
        },
        {
            "knowledge_entry_id": "know-travel-p4-tier1",
            "document_title": "《差旅管理制度（2024 版）》",
            "section": "第 3.2 条 员工住宿标准",
            "excerpt": "职级 P4 及以上在一线城市住宿限额 1200 元/晚。",
            "city_type": "一线城市",
            "level": "P4 及以上",
            "limit_cny": 1200,
            "is_active": 1,
        },
        {
            "knowledge_entry_id": "know-travel-reimburse",
            "document_title": "《费用报销规范》",
            "section": "第 2.1 条 差旅费用报销要求",
            "excerpt": "差旅住宿以职级与城市类型对照表执行，限额见差旅管理制度。",
            "city_type": None,
            "level": None,
            "limit_cny": None,
            "is_active": 1,
        },
    ]
    for row in rows:
        entry_id = str(row.pop("knowledge_entry_id"))
        await _upsert(session, KnowledgeEntry, "knowledge_entry_id", entry_id, row)


async def _seed_people(session: AsyncSession, app_settings: AppSettings) -> None:
    name = app_settings.meeting_disambiguation_person_name
    await _upsert(
        session,
        Person,
        "person_id",
        "person-zhangming-product",
        {
            "display_name": name,
            "department": app_settings.mock_user_department,
            "job_title": None,
        },
    )
    await _upsert(
        session,
        Person,
        "person_id",
        "person-zhangming-finance",
        {
            "display_name": name,
            "department": _FINANCE_DEPARTMENT,
            "job_title": None,
        },
    )


async def _seed_meeting_rooms(session: AsyncSession, app_settings: AppSettings) -> None:
    after_hour = app_settings.meeting_room_query_after_hour
    offset_days = app_settings.meeting_room_query_demo_date_offset_days
    xinghe_from, xinghe_to = _demo_room_window(
        after_hour, offset_days, _ROOM_XINGHE_DURATION_MINUTES
    )
    qihang_from, qihang_to = _demo_room_window(
        after_hour, offset_days, _ROOM_QIHANG_DURATION_MINUTES
    )
    await _upsert(
        session,
        MeetingRoom,
        "room_id",
        "room-xinghe-3",
        {
            "room_name": "星河 3 号",
            "available_from": xinghe_from,
            "available_to": xinghe_to,
            "tomorrow_after_hour": after_hour,
        },
    )
    await _upsert(
        session,
        MeetingRoom,
        "room_id",
        "room-qihang",
        {
            "room_name": "启航厅",
            "available_from": qihang_from,
            "available_to": qihang_to,
            "tomorrow_after_hour": after_hour,
        },
    )


async def _seed_work_messages(session: AsyncSession, app_settings: AppSettings) -> None:
    now = datetime.now(UTC)
    messages = [
        (
            "msg-work-arch",
            "work",
            "完成 Aily 工作台信息架构评审",
            now - timedelta(hours=2),
        ),
        (
            "msg-work-zhangming",
            "work",
            "与张明对齐项目复盘会材料",
            now - timedelta(hours=1),
        ),
        (
            "msg-chitchat-dinner",
            "chitchat",
            "晚上吃啥",
            now - timedelta(minutes=30),
        ),
    ]
    for message_id, kind, content, occurred in messages:
        await _upsert(
            session,
            WorkMessage,
            "message_id",
            message_id,
            {
                "user_id": app_settings.mock_user_id,
                "occurred_at": format_utc_z(occurred),
                "kind": kind,
                "content": content,
                "is_this_week": 1,
            },
        )


async def _seed_evaluation_cases(session: AsyncSession, app_settings: AppSettings) -> None:
    cases: list[dict[str, Any]] = [
        {
            "case_id": "eval-qa-travel",
            "name": "差旅住宿标准",
            "scene_id": "S-001",
            "query": "公司的差旅住宿标准是什么？",
            "expected_route": "企业知识",
            "actual_route": "企业知识",
            "passed": 1,
            "bad_case_category": "none",
            "replay_turn_id": "turn-eval-qa-travel",
        },
        {
            "case_id": "eval-qa-refuse",
            "name": "无依据问句拒答",
            "scene_id": "S-002",
            "query": app_settings.knowledge_refuse_demo_query,
            "expected_route": "企业知识-拒答",
            "actual_route": "企业知识-拒答",
            "passed": 1,
            "bad_case_category": "no_evidence_refusal",
            "replay_turn_id": "turn-eval-qa-refuse",
        },
        {
            "case_id": "eval-meeting-success",
            "name": "创建项目复盘会",
            "scene_id": "S-003",
            "query": "帮我明天下午三点跟张明开一个项目复盘会。",
            "expected_route": "技能 create_meeting",
            "actual_route": "技能 create_meeting",
            "passed": 1,
            "bad_case_category": "none",
            "replay_turn_id": "turn-eval-meeting-success",
        },
        {
            "case_id": "eval-meeting-timeout",
            "name": "创建会议超时",
            "scene_id": "S-006",
            "query": "帮我约明天下午 3 点和张明开项目复盘会",
            "expected_route": "技能 create_meeting → 未知",
            "actual_route": "技能 create_meeting → 未知",
            "passed": 1,
            "bad_case_category": "timeout_unknown",
            "replay_turn_id": "turn-eval-timeout",
        },
        {
            "case_id": "eval-meeting-stale",
            "name": "改时间后重确认",
            "scene_id": "S-007",
            "query": "改成明天下午两点吧。",
            "expected_route": "确认作废后重确认",
            "actual_route": "确认作废后重确认",
            "passed": 1,
            "bad_case_category": "confirmation_invalidated",
            "replay_turn_id": "turn-eval-stale",
        },
        {
            "case_id": "eval-report",
            "name": "生成本周周报",
            "scene_id": "S-004",
            "query": "帮我生成本周周报。",
            "expected_route": "技能 generate_work_report",
            "actual_route": "技能 generate_work_report",
            "passed": 1,
            "bad_case_category": "none",
            "replay_turn_id": "turn-eval-report",
        },
        {
            "case_id": "eval-rooms",
            "name": "查询可用会议室",
            "scene_id": "S-005",
            "query": "查询明天下午 3 点以后可用的会议室",
            "expected_route": "只读查询",
            "actual_route": "只读查询",
            "passed": 1,
            "bad_case_category": "none",
            "replay_turn_id": "turn-eval-rooms",
        },
    ]
    if len(cases) != app_settings.evaluation_case_count_expected:
        raise ValueError("评测案例种子条数必须等于 EVALUATION_CASE_COUNT_EXPECTED")
    canonical_ids = {str(item["case_id"]) for item in cases}
    existing_rows = (await session.execute(select(EvaluationCase))).scalars().all()
    for row in existing_rows:
        if row.case_id not in canonical_ids:
            await session.delete(row)
    for item in cases:
        case_id = str(item.pop("case_id"))
        await _upsert(session, EvaluationCase, "case_id", case_id, item)


async def _seed_timeout_conversation(session: AsyncSession, app_settings: AppSettings) -> None:
    now = utc_now_iso()
    conversation_id = app_settings.meeting_timeout_demo_conversation_id
    existing = (
        await session.execute(
            select(Conversation).where(Conversation.conversation_id == conversation_id)
        )
    ).scalar_one_or_none()
    values = {
        "user_id": app_settings.mock_user_id,
        "title": "会议超时演示",
        "preview": "帮我约明天下午 3 点和张明开项目复盘会",
        "updated_at": now,
    }
    if existing is None:
        values["created_at"] = now
        session.add(Conversation(conversation_id=conversation_id, **values))
        return
    for field, value in values.items():
        setattr(existing, field, value)


async def seed_database(
    session: AsyncSession, app_settings: AppSettings | None = None
) -> None:
    """写入或更新预置数据，可重复执行。不 drop 表、不删除用户对话。"""
    cfg = app_settings if app_settings is not None else settings
    await _seed_knowledge(session)
    await _seed_people(session, cfg)
    await _seed_meeting_rooms(session, cfg)
    await _seed_work_messages(session, cfg)
    await _seed_evaluation_cases(session, cfg)
    await _seed_timeout_conversation(session, cfg)
    get_logger().info(
        "种子数据已写入",
        timeout_conversation_id=cfg.meeting_timeout_demo_conversation_id,
        evaluation_case_count=cfg.evaluation_case_count_expected,
    )
