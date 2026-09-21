"""固定链路 Agent 编排。不使用开放规划框架。"""

from pycore.core import ConfigurationError, get_logger
from pycore.plugins import PluginRegistry

from src.core.config import AppSettings, settings
from src.models.agent.types import (
    AssistantMessage,
    ConversationRuntimeState,
    IntentResult,
    OrchestratorState,
    QueryContext,
    RouteDecision,
    TurnResponse,
)
from src.plugins.registry import get_plugin_registry, register_agent_plugins

logger = get_logger()

_BRANCH = {
    "RAG": "rag",
    "SKILL": "skill",
    "READ_TOOL": "read_tool",
}


class AgentOrchestratorService:
    """按 tech-spec §3 固定顺序调用 PluginRegistry，只追加真实 TraceEvent。"""

    def __init__(
        self,
        registry: PluginRegistry | None = None,
        app_settings: AppSettings | None = None,
    ) -> None:
        self._settings = app_settings if app_settings is not None else settings
        self._registry = registry if registry is not None else get_plugin_registry()

    async def run(
        self,
        query: QueryContext,
        conversation_state: ConversationRuntimeState | None = None,
    ) -> TurnResponse:
        if not self._settings.mock_mode:
            raise ConfigurationError("MVP 仅支持 MOCK_MODE=true 的 deterministic adapter")
        register_agent_plugins(self._registry)
        state = OrchestratorState(
            query=query,
            conversation_state=conversation_state or ConversationRuntimeState(),
        )
        await self._execute("rewrite", state)
        await self._execute("intent", state)
        await self._execute("slot", state)
        await self._execute("memory", state)
        if state.intent is not None and state.intent.operation_type == "WRITE":
            await self._execute("risk_permission", state)
        await self._execute("router", state)
        if state.route is None:
            raise ValueError("路由节点未产出 RouteDecision")
        branch = _BRANCH.get(state.route.route_type)
        if branch is None:
            raise ValueError(f"未知路由类型: {state.route.route_type}")
        await self._execute(branch, state)
        await self._execute("result_validation", state)
        logger.info(
            "Agent 固定链路执行完成",
            conversation_id=query.conversation_id,
            turn_id=query.turn_id,
            event_count=len(state.trace_events),
        )
        return self._to_response(state)

    async def _execute(self, name: str, state: OrchestratorState) -> None:
        result = await self._registry.execute(name, state=state)
        if not result:
            raise ValueError(result.error or f"Plugin {name} 执行失败")

    def _to_response(self, state: OrchestratorState) -> TurnResponse:
        intent = state.intent or IntentResult(intent="unknown", operation_type="READ", confidence=1.0)
        route = state.route or RouteDecision(
            route_type="RAG",
            target="enterprise_knowledge",
            display_route="企业知识",
        )
        validation = state.validation
        assistant = (
            validation.assistant_message
            if validation is not None
            else AssistantMessage(message_type="empty")
        )
        status = validation.status if validation is not None else "processing"
        citations = validation.citations if validation is not None else []
        slot_state = state.slot_result.slot_state if state.slot_result is not None else None
        return TurnResponse(
            turn_id=state.query.turn_id,
            conversation_id=state.query.conversation_id,
            status=status,
            user_message=state.query.raw_query,
            assistant_message=assistant,
            citations=citations,
            route_decision=route,
            trace_events=list(state.trace_events),
            intent=intent,
            slot_state=slot_state,
        )
