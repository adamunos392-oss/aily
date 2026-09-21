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
        _append(
            state,
            "intent",
            "意图识别",
            f"{state.intent.intent} / {state.intent.operation_type}",
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
            "槽位已更新" if state.slot_result.slot_state.slots else "本轮无业务槽位",
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
        if state.route.route_type == "SKILL":
            title = f"路由到{state.route.display_route}"
        elif state.route.route_type == "READ_TOOL":
            title = "只读查询"
        _append(
            state,
            "router",
            title,
            state.route.display_route,
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
            state.skill.skill_id,
            {"skill_id": state.skill.skill_id, "status": state.skill.status},
        )
        if state.skill.tool_calls:
            results = await service.run_tools(state.skill.tool_calls, state.query)
            state.tool_results.extend(results)
            for result in results:
                _append(
                    state,
                    "tool_call",
                    "工具调用" if result.status != "timeout" else "原子能力超时",
                    result.status,
                    {"tool_id": result.tool_id, "status": result.status},
                )
        if state.skill.confirmation is not None:
            _append(
                state,
                "confirmation",
                "待确认",
                state.skill.confirmation.status,
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
        _append(
            state,
            "tool_call",
            "查询会议室",
            result.status,
            {"tool_id": result.tool_id, "status": result.status},
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
            state.validation.result_status,
            {"status": state.validation.status, "result_status": state.validation.result_status},
        )
        final_title = "最终结果"
        if state.validation.status == "refused":
            final_title = "最终已拒答"
        elif state.validation.status == "unknown":
            final_title = "最终未知 · 无会议已创建"
        _append(
            state,
            "final",
            final_title,
            state.validation.status,
            {"status": state.validation.status},
        )
        return self.success(state)
