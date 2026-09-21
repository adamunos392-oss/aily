"""Mock Adapter 确定性 ID / 时间 / 摘要截断。读取 AppSettings，禁止硬编码种子与截断长度。"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from src.core.config import AppSettings, settings
from src.models.agent.types import TraceEvent, TraceNode


def stable_digest(app_settings: AppSettings, *parts: object) -> str:
    """相同 seed + parts 得到相同短摘要。"""
    material = json.dumps(
        [app_settings.mock_deterministic_seed, *[str(part) for part in parts]],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:12]


def stable_id(prefix: str, app_settings: AppSettings, *parts: object) -> str:
    return f"{prefix}-{stable_digest(app_settings, prefix, *parts)}"


def truncate_text(text: str, app_settings: AppSettings) -> str:
    limit = app_settings.trace_event_detail_max_chars
    if len(text) <= limit:
        return text
    return text[:limit]


def event_time(app_settings: AppSettings, sequence: int) -> datetime:
    base = datetime(2026, 9, 21, 2, 0, 0, tzinfo=UTC)
    return base + timedelta(seconds=app_settings.mock_deterministic_seed + sequence)


def make_trace_event(
    *,
    turn_id: str,
    sequence: int,
    node: TraceNode,
    title_zh: str,
    summary: str,
    payload: dict[str, Any] | None = None,
    app_settings: AppSettings | None = None,
) -> TraceEvent:
    cfg = app_settings if app_settings is not None else settings
    body = payload if payload is not None else {}
    return TraceEvent(
        event_id=f"evt-{turn_id}-{sequence}",
        turn_id=turn_id,
        sequence=sequence,
        occurred_at=event_time(cfg, sequence),
        node=node,
        title_zh=title_zh,
        summary=truncate_text(summary, cfg),
        payload=body,
    )
