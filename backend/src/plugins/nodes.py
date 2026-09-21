"""Agent 节点 Plugin。调用对应 Service，不直接碰 Adapter。"""

from typing import Any

from pycore.plugins import BasePlugin, PluginResult

from src.core.config import settings as app_settings
from src.models.agent.types import OrchestratorState, ToolCall, TraceNode
from src.repositories.mock.ids import make_trace_event, stable_id
from src.services.agent_nodes import (
    IntentService,
    MemoryService,
    RagService,
    ResultValidationService,
    RewriteService,
    RiskPermissionService,
    RouterService,
    SkillService,
    SlotService,
    ToolService,
)


def _append(
    state: OrchestratorState,
    node: TraceNode,
    title_zh: str,
    summary: str,
    payload: dict[str, Any] | None = None,
) -> None:
    state.sequence += 1
    state.trace_events.append(
        make_trace_event(
            turn_id=state.query.turn_id,
            sequence=state.sequence,
            node=node,
            title_zh=title_zh,
            summary=summary,
            payload=payload,
        )
    )


def _clock_label(value: object) -> str:
    text = str(value or "")
    if "14:00" in text:
        return "14:00"
    if "15:00" in text:
        return "15:00"
    return text or "—"


def _slot_summary(state: OrchestratorState) -> str:
    result = state.slot_result
    if result is None:
        return "本轮无业务槽位"
    if state.intent is None or state.intent.intent != "create_meeting":
        return "槽位已更新" if result.slot_state.slots else "本轮无业务槽位"
    if result.key_slot_changed and state.conversation_state.slot_state is not None:
        old = _clock_label(state.conversation_state.slot_state.slots.get("meeting_time"))
        new = _clock_label(result.slot_state.slots.get("meeting_time"))
        return f"会议时间由 {old} 改为 {new}"
    if result.slot_state.missing_required:
        return "已填：参会人张明（未消歧）　缺失：时间、主题"
    if result.needs_disambiguation:
        return "时间已填，参会人存在同名"
    return "槽位已齐"


def _skill_summary(state: OrchestratorState) -> str:
    skill = state.skill
    if skill is None:
        return "技能"
    if skill.skill_id == app_settings.weekly_report_skill_id:
        return "生成工作周报 · 套用简洁中文事项列表"
    if skill.skill_id != app_settings.create_meeting_skill_id:
        return skill.skill_id
    if skill.message_type == "disambiguation":
        return "创建会议 · 等待选定人员"
    if skill.message_type == "clarification":
        return "创建会议 · 等待补全槽位"
    return "创建会议 · 编排找人、日历、会议"


def _tool_event(result: Any) -> tuple[str, str]:
    if result.status == "timeout":
        return "原子能力超时", "创建会议超时"
    if result.tool_id == "people_lookup":
        return "原子能力", "找人成功"
    if result.tool_id == "calendar_check":
        return "原子能力", "日历可写"
    if result.tool_id == "meeting_create":
        return "原子能力", "会议已写入"
    if result.tool_id == "work_message_fetch":
        return "原子能力", "已取本周工作消息"
    return "工具调用", str(result.status)


def _result_status_zh(status: str) -> str:
    mapping = {
        "success": "成功",
        "unknown": "未知",
        "pending": "待确认",
        "refused": "未通过",
    }
    return mapping.get(status, status)


class RewritePlugin(BasePlugin):
    name: str = "rewrite"
    description: str = "问题改写"

    async def execute(self, state: OrchestratorState, **kwargs: Any) -> PluginResult:
        service: RewriteService = kwargs.get("rewrite_service") or RewriteService()
        state.rewrite = await service.rewrite(state.query)
        _append(
            state,
            "query_rewrite",
            "问题改写",
            state.rewrite.rewritten_query,
            {"rewritten_query": state.rewrite.rewritten_query},
        )
        return self.success(state)


class IntentPlugin(BasePlugin):
    name: str = "intent"
    description: str = "意图识别"

    async def execute(self, state: OrchestratorState, **kwargs: Any) -> PluginResult:
        service: IntentService = kwargs.get("intent_service") or IntentService()
        rewritten = state.rewrite.rewritten_query if state.rewrite is not None else state.query.raw_query
        state.intent = await service.classify(state.query, rewritten)
        summary = f"{state.intent.intent} / {state.intent.operation_type}"
        if state.intent.intent == "query_meeting_rooms":
            summary = "意图：查询会议室\u3000只读"
        elif state.intent.intent == "generate_work_report":
            summary = "意图：生成周报\u3000只读"
        elif state.intent.intent == "create_meeting":
            summary = "意图：创建会议\u3000写入"
        _append(
            state,
            "intent",
            "意图识别",
            summary,
            {"intent": state.intent.intent, "operation_type": state.intent.operation_type},
        )
        return self.success(state)


class SlotPlugin(BasePlugin):
    name: str = "slot"
    description: str = "槽位填充"

    async def execute(self, state: OrchestratorState, **kwargs: Any) -> PluginResult:
        if state.intent is None:
            return self.fail("意图尚未识别，无法填槽")
        service: SlotService = kwargs.get("slot_service") or SlotService()
        rewritten = state.rewrite.rewritten_query if state.rewrite is not None else state.query.raw_query
        state.slot_result = await service.fill(
            state.query, state.intent, rewritten, state.conversation_state
        )
        _append(
            state,
            "slot_fill",
            "槽位填充",
            _slot_summary(state),
            {
                "is_complete": state.slot_result.slot_state.is_complete,
                "missing_required": state.slot_result.slot_state.missing_required,
            },
        )
        return self.success(state)


class MemoryPlugin(BasePlugin):
    name: str = "memory"
    description: str = "读取稳定偏好记忆"

    async def execute(self, state: OrchestratorState, **kwargs: Any) -> PluginResult:
        service: MemoryService = kwargs.get("memory_service") or MemoryService()
        state.memory_state = await service.load()
        _append(
            state,
            "memory",
            "记忆",
            "读取模板/语言/篇幅偏好",
            {
                "template_style": state.memory_state.template_style,
                "language": state.memory_state.language,
                "length": state.memory_state.length,
            },
        )
        return self.success(state)


class RiskPermissionPlugin(BasePlugin):
    name: str = "risk_permission"
    description: str = "写操作风险与权限"

    async def execute(self, state: OrchestratorState, **kwargs: Any) -> PluginResult:
        if state.intent is None:
            return self.fail("意图尚未识别，无法做风险权限检查")
        service: RiskPermissionService = kwargs.get("risk_service") or RiskPermissionService()
        state.risk = await service.check(state.intent)
        _append(
            state,
            "risk_permission",
            "风险与权限",
            state.risk.summary,
            {"allowed": state.risk.allowed, "operation_type": state.risk.operation_type},
        )
        return self.success(state)


class RouterPlugin(BasePlugin):
    name: str = "router"
    description: str = "路由决策"

    async def execute(self, state: OrchestratorState, **kwargs: Any) -> PluginResult:
        if state.intent is None:
            return self.fail("意图尚未识别，无法路由")
        service: RouterService = kwargs.get("router_service") or RouterService()
        rewritten = state.rewrite.rewritten_query if state.rewrite is not None else state.query.raw_query
        state.route = await service.decide(state.intent, rewritten, state.query.entry_source)
        title = "路由到企业知识"
        summary = state.route.display_route
        if state.route.route_type == "SKILL":
            if state.intent.intent == "generate_work_report":
                title = "路由"
                summary = "技能：生成工作周报"
            else:
                title = f"路由到{state.route.display_route}"
        elif state.route.route_type == "READ_TOOL":
            title = "路由"
        _append(
            state,
            "router",
            title,
            summary,
            {"route_type": state.route.route_type, "target": state.route.target},
        )
        return self.success(state)


class RagPlugin(BasePlugin):
    name: str = "rag"
    description: str = "企业知识检索"

    async def execute(self, state: OrchestratorState, **kwargs: Any) -> PluginResult:
        service: RagService = kwargs.get("rag_service") or RagService()
        rewritten = state.rewrite.rewritten_query if state.rewrite is not None else state.query.raw_query
        state.rag = await service.retrieve(state.query, rewritten)
        title = "知识检索" if state.rag.hit_count else "知识检索未命中"
        _append(
            state,
            "rag_retrieve",
            title,
            f"命中 {state.rag.hit_count} 条",
            {"hit_count": state.rag.hit_count},
        )
        return self.success(state)


class SkillPlugin(BasePlugin):
    name: str = "skill"
    description: str = "技能固定编排"

    async def execute(self, state: OrchestratorState, **kwargs: Any) -> PluginResult:
        if state.intent is None or state.slot_result is None:
            return self.fail("意图或槽位缺失，无法执行技能")
        service: SkillService = kwargs.get("skill_service") or SkillService()
        state.skill = await service.plan(
            state.query, state.intent, state.slot_result, state.conversation_state
        )
        _append(
            state,
            "skill",
            "技能",
            _skill_summary(state),
            {"skill_id": state.skill.skill_id, "status": state.skill.status},
        )
        if state.skill.tool_calls:
            results = await service.run_tools(state.skill.tool_calls, state.query)
            state.tool_results.extend(results)
            for result in results:
                title_zh, summary = _tool_event(result)
                _append(
                    state,
                    "tool_call",
                    title_zh,
                    summary,
                    {"tool_id": result.tool_id, "status": result.status},
                )
        if state.skill.skill_id == app_settings.weekly_report_skill_id:
            state.skill.report_draft = service.compose_weekly_report(
                state.query, state.tool_results, state.memory_state
            )
            for step_summary, step_id in (
                ("过滤闲聊", "filter_chitchat"),
                ("抽取工作事项", "extract_items"),
                ("套用简洁中文事项列表", "apply_template"),
                ("润色", "polish"),
            ):
                _append(
                    state,
                    "skill",
                    "技能",
                    step_summary,
                    {"skill_id": state.skill.skill_id, "step": step_id},
                )
        old_confirmation = state.conversation_state.active_confirmation
        if (
            state.slot_result.key_slot_changed
            and old_confirmation is not None
            and old_confirmation.status == "pending"
        ):
            _append(
                state,
                "confirmation",
                "确认",
                "原确认已作废",
                {
                    "confirmation_id": old_confirmation.confirmation_id,
                    "status": "invalidated",
                    "meeting_time": _clock_label(old_confirmation.meeting_time),
                },
            )
        if state.skill.confirmation is not None:
            _append(
                state,
                "confirmation",
                "确认",
                "状态：待确认",
                {
                    "confirmation_id": state.skill.confirmation.confirmation_id,
                    "status": state.skill.confirmation.status,
                },
            )
        return self.success(state)


class ReadToolPlugin(BasePlugin):
    name: str = "read_tool"
    description: str = "只读查询原子 Tool"

    async def execute(self, state: OrchestratorState, **kwargs: Any) -> PluginResult:
        service: ToolService = kwargs.get("tool_service") or ToolService()
        call = ToolCall(
            tool_id="meeting_room_query",
            arguments={"after_hour": app_settings.meeting_room_query_after_hour},
            call_id=stable_id("call", app_settings, state.query.turn_id, "meeting_room_query"),
        )
        result = await service.execute(call, state.query)
        state.tool_results.append(result)
        rooms = []
        if result.payload and isinstance(result.payload.get("rooms"), list):
            rooms = result.payload["rooms"]
        summary = "查询会议室成功" if rooms else "查询会议室 · 无空闲"
        _append(
            state,
            "tool_call",
            "原子能力",
            summary,
            {"tool_id": result.tool_id, "status": result.status, "room_count": len(rooms)},
        )
        return self.success(state)


class ResultValidationPlugin(BasePlugin):
    name: str = "result_validation"
    description: str = "结果核验"

    async def execute(self, state: OrchestratorState, **kwargs: Any) -> PluginResult:
        if state.route is None:
            return self.fail("路由缺失，无法核验")
        service: ResultValidationService = kwargs.get("validation_service") or ResultValidationService()
        state.validation = await service.validate(
            route=state.route,
            rag=state.rag,
            skill=state.skill,
            tool_results=state.tool_results,
        )
        if state.route.route_type == "RAG":
            valid = bool(state.validation.citation_valid)
            _append(
                state,
                "citation_validate",
                "引用核验通过" if valid else "引用核验未通过",
                "引用通过" if valid else "引用未通过",
                {"valid": valid},
            )
        _append(
            state,
            "result_validate",
            "结果核验",
            _result_status_zh(state.validation.result_status),
            {"status": state.validation.status, "result_status": state.validation.result_status},
        )
        final_title = "最终结果"
        final_summary: str = str(state.validation.status)
        if state.validation.status == "refused":
            final_title = "最终已拒答"
            final_summary = "已拒答"
        elif state.validation.status == "unknown":
            final_summary = "未知 · 待核验"
        elif state.validation.status == "awaiting_confirmation":
            final_summary = "待确认 · 尚未创建"
        elif state.validation.status == "clarifying":
            final_summary = "待澄清"
        elif state.route.route_type == "READ_TOOL":
            rooms = state.validation.assistant_message.rooms or []
            final_summary = (
                "已回复 · 未创建会议" if rooms else "已回复 · 未预订、未创建会议"
            )
        elif state.validation.assistant_message.message_type == "meeting_success":
            final_summary = "已回复 · 会议已创建"
        elif state.validation.assistant_message.message_type == "report_draft":
            final_summary = "已回复 · 可编辑周报"
        _append(
            state,
            "final",
            final_title,
            final_summary,
            {"status": state.validation.status},
        )
        return self.success(state)
