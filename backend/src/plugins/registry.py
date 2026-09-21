"""PluginRegistry 注册固定 Agent 节点链路。"""

from pycore.plugins import BasePlugin, PluginRegistry

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

AGENT_PLUGIN_NAMES: tuple[str, ...] = (
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

_registry: PluginRegistry | None = None


def build_agent_plugins() -> list[BasePlugin]:
    return [
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


def get_plugin_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


def register_agent_plugins(registry: PluginRegistry | None = None) -> PluginRegistry:
    """幂等注册全部 Agent 节点 Plugin，顺序与 tech-spec §3 一致。"""
    target = registry if registry is not None else get_plugin_registry()
    for plugin in build_agent_plugins():
        if not target.has(plugin.name):
            target.register(plugin)
    return target
