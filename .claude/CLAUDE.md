# SDD Harness V7_2 — Claude Code Entry

你是 SDD Harness V7_2 在 Claude Code 环境下的入口。

核心规则只允许维护在 `harness-core/`。`.claude/` 目录只做 Claude Code 适配。

## 启动顺序

处理任何项目管理、产品设计、功能升级、Bugfix、开发任务前，先读取：

1. `harness-core/router.md`
2. `harness-core/protocols/development-rules.md`

## Agents

Claude Code agent 适配器位于：

```text
.claude/agents/planner.md
.claude/agents/developer.md
.claude/agents/tester.md
.claude/agents/solution-designer.md
```

这些文件只引用：

```text
harness-core/agents/*.md
```

不要在 `.claude/agents/` 里维护核心规则。

## 开发循环入口

多智能体开发循环由语义路由触发，无命令层。协议本体位于：

```text
harness-core/protocols/development-loop.md
```

`sdd-start` / `sdd-new-project` / `sdd-align` / `sdd-bugfix` 命令已移除，由 Router 直接路由：开发循环走 `harness-core/protocols/development-loop.md`，新建项目走 `scripts/sdd_project.py new`（见 `harness-core/router.md`），Bugfix 走 `harness-core/skills/sdd-bugfix/SKILL.md`。
