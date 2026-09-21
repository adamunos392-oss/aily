"""PluginRegistry 注册与启动注册测试。"""

from pathlib import Path

from fastapi.testclient import TestClient
from pycore.plugins import BasePlugin

from src.main import app
from src.plugins.nodes import (
    IntentPlugin,
    MemoryPlugin,
    RagPlugin,
    ReadToolPlugin,
    ResultValidationPlugin,
    RewritePlugin,
    RiskPermissionPlugin,
    RouterPlugin,
    SkillPlugin,
    SlotPlugin,
)
from src.plugins.registry import AGENT_PLUGIN_NAMES, get_plugin_registry, register_agent_plugins

BACKEND_SRC = Path(__file__).resolve().parents[1] / "src"
FORBIDDEN_IMPORT_PREFIXES = ("import langgraph", "from langgraph", "import langchain", "from langchain")


def test_agent_plugin_order_matches_tech_spec() -> None:
    assert AGENT_PLUGIN_NAMES == (
        "rewrite",
        "intent",
        "slot",
        "memory",
        "risk_permission",
        "router",
        "rag",
        "skill",
        "read_tool",
        "result_validation",
    )


def test_plugin_classes_exist() -> None:
    plugins: list[BasePlugin] = [
        RewritePlugin(),
        IntentPlugin(),
        SlotPlugin(),
        MemoryPlugin(),
        RiskPermissionPlugin(),
        RouterPlugin(),
        RagPlugin(),
        SkillPlugin(),
        ReadToolPlugin(),
        ResultValidationPlugin(),
    ]
    assert [item.name for item in plugins] == list(AGENT_PLUGIN_NAMES)


def test_startup_registers_all_plugins() -> None:
    with TestClient(app):
        registry = get_plugin_registry()
        assert registry.list_plugins() == list(AGENT_PLUGIN_NAMES)
        assert len(registry) == len(AGENT_PLUGIN_NAMES)


def test_register_agent_plugins_is_idempotent() -> None:
    first = register_agent_plugins()
    second = register_agent_plugins()
    assert first is second
    assert len(first) == len(AGENT_PLUGIN_NAMES)


def test_source_has_no_open_planning_frameworks() -> None:
    hits: list[str] = []
    for path in BACKEND_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for token in FORBIDDEN_IMPORT_PREFIXES:
            if token in lowered:
                hits.append(f"{path}: {token}")
    assert hits == []
