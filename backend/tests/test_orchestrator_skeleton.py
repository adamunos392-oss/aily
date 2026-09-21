"""AgentOrchestrator 固定链路骨架测试。"""

from pathlib import Path

import pytest

from src.core.config import settings
from src.models.agent.types import ConversationRuntimeState, QueryContext
from src.repositories.mock import (
    EvaluationAdapter,
    IntentAdapter,
    RagAdapter,
    RewriteAdapter,
    RouterAdapter,
    SkillAdapter,
    SlotAdapter,
    ToolAdapter,
)
from src.services.agent_orchestrator import AgentOrchestratorService

MOCK_DIR = Path(__file__).resolve().parents[1] / "src" / "repositories" / "mock"
ADAPTER_FILES = (
    "rewrite_adapter.py",
    "intent_adapter.py",
    "slot_adapter.py",
    "router_adapter.py",
    "rag_adapter.py",
    "tool_adapter.py",
    "skill_adapter.py",
    "evaluation_adapter.py",
)


def _query(text: str, turn_id: str, conversation_id: str = "conv-t005") -> QueryContext:
    return QueryContext(
        conversation_id=conversation_id,
        turn_id=turn_id,
        raw_query=text,
        entry_source="manual",
        user_id=settings.mock_user_id,
    )


@pytest.fixture
def orchestrator() -> AgentOrchestratorService:
    return AgentOrchestratorService()


def test_eight_mock_adapters_exist() -> None:
    for name in ADAPTER_FILES:
        assert (MOCK_DIR / name).is_file()
    assert RewriteAdapter is not None
    assert IntentAdapter is not None
    assert SlotAdapter is not None
    assert RouterAdapter is not None
    assert RagAdapter is not None
    assert ToolAdapter is not None
    assert SkillAdapter is not None
    assert EvaluationAdapter is not None


@pytest.mark.asyncio
async def test_travel_read_path_has_no_confirmation(orchestrator: AgentOrchestratorService) -> None:
    result = await orchestrator.run(_query("公司的差旅住宿标准是什么？", "turn-travel"))
    nodes = [event.node for event in result.trace_events]
    assert "confirmation" not in nodes
    assert "risk_permission" not in nodes
    assert nodes[0] == "query_rewrite"
    assert "intent" in nodes
    assert "slot_fill" in nodes
    assert "memory" in nodes
    assert "router" in nodes
    assert "rag_retrieve" in nodes
    assert "citation_validate" in nodes
    assert "final" in nodes
    assert result.intent.operation_type == "READ"
    assert result.route_decision.route_type == "RAG"
    assert result.status == "replied"
    assert result.assistant_message.confirmation is None


@pytest.mark.asyncio
async def test_refuse_and_rooms_read_paths_have_no_confirmation(
    orchestrator: AgentOrchestratorService,
) -> None:
    refuse = await orchestrator.run(_query(settings.knowledge_refuse_demo_query, "turn-refuse"))
    rooms = await orchestrator.run(_query("查询明天下午 3 点以后可用的会议室", "turn-rooms"))
    assert "confirmation" not in [event.node for event in refuse.trace_events]
    assert "confirmation" not in [event.node for event in rooms.trace_events]
    assert refuse.status == "refused"
    assert rooms.status == "replied"
    assert rooms.assistant_message.message_type == "room_list"
    assert rooms.assistant_message.confirmation is None
    assert rooms.route_decision.route_type == "READ_TOOL"


@pytest.mark.asyncio
async def test_same_input_is_deterministic(orchestrator: AgentOrchestratorService) -> None:
    first = await orchestrator.run(_query("公司的差旅住宿标准是什么？", "turn-stable"))
    second = await orchestrator.run(_query("公司的差旅住宿标准是什么？", "turn-stable"))
    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert settings.mock_mode is True
    assert first.trace_events[0].payload["rewritten_query"] == "差旅住宿标准"


@pytest.mark.asyncio
async def test_write_meeting_with_choice_emits_confirmation(
    orchestrator: AgentOrchestratorService,
) -> None:
    result = await orchestrator.run(
        _query("帮我明天下午三点跟张明开一个项目复盘会。", "turn-meet"),
        ConversationRuntimeState(choice_id="person:zhangming-product"),
    )
    nodes = [event.node for event in result.trace_events]
    assert "risk_permission" in nodes
    assert "confirmation" in nodes
    assert result.intent.operation_type == "WRITE"
    assert result.route_decision.route_type == "SKILL"
    assert result.status == "awaiting_confirmation"


@pytest.mark.asyncio
async def test_evaluation_adapter_count_and_read_cases_skip_confirmation() -> None:
    cases = await EvaluationAdapter().list_cases()
    assert len(cases) == settings.evaluation_case_count_expected
    by_id = {item.case_id: item for item in cases}
    travel_nodes = [event.node for event in by_id["eval-qa-travel"].trace_events]
    rooms_nodes = [event.node for event in by_id["eval-rooms"].trace_events]
    refuse_nodes = [event.node for event in by_id["eval-qa-refuse"].trace_events]
    assert "confirmation" not in travel_nodes
    assert "confirmation" not in rooms_nodes
    assert "confirmation" not in refuse_nodes


def test_orchestrator_source_is_fixed_pipeline() -> None:
    source = (
        Path(__file__).resolve().parents[1] / "src" / "services" / "agent_orchestrator.py"
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    assert "import langgraph" not in lowered
    assert "from langgraph" not in lowered
    assert "import langchain" not in lowered
    assert "from langchain" not in lowered
    assert "rewrite" in source
    assert "result_validation" in source
