# SDD Harness V7_2 — Codex Entry

你是 SDD Harness V7_2 在 Codex 环境下的入口。

本项目支持 Codex / Claude Code / Cursor 三端使用。核心规则只允许维护在 `harness-core/`，平台目录只做适配。

## 启动顺序

处理任何项目管理、产品设计、功能升级、Bugfix、开发任务前，先读取：

1. `harness-core/router.md`
2. `harness-core/protocols/development-rules.md`
3. 如需多智能体开发，读取 `harness-core/protocols/codex-subagents.md`

## 开发循环入口

多智能体开发循环由语义路由触发，无命令层。协议本体位于：

```text
harness-core/protocols/development-loop.md
```

`sdd-start` / `sdd-new-project` / `sdd-align` / `sdd-bugfix` 命令已移除，由 Router 直接路由：开发循环走 `harness-core/protocols/development-loop.md`，新建项目走 `scripts/sdd_project.py new`（见 `harness-core/router.md`），Bugfix 走 `harness-core/skills/sdd-bugfix/SKILL.md`。

## Codex Subagents

Codex subagent 配置位于：

```text
.codex/agents/planner.toml
.codex/agents/developer.toml
.codex/agents/tester.toml
.codex/agents/solution-designer.toml
```

当用户说“开始开发 / 进入开发阶段 / 继续多智能体开发”时，视为明确授权 Codex 使用 subagents：

- `planner`
- `developer`
- `tester`

按 `harness-core/protocols/development-loop.md` 和 `harness-core/protocols/codex-subagents.md` 推进。若当前 Codex 环境不支持自定义 subagent TOML，在主会话中模拟 Planner / Developer / Tester，但必须保持角色边界。

另外，产品设计的阶段 TS（技术方案）在 B2 原型确认后由 Router 派出 `solution-designer`（定义见 `harness-core/agents/solution-designer.md`），产出 `docs/tech-spec.md`，不依赖开发授权。

## 路径原则

业务文件只能写入当前活动项目：

```text
Projects_Repo/<active_project_id>/
```

不得把业务 `docs/`、`.sdd/`、`frontend/`、`backend/` 写到 Harness 根目录。

## 核心规则位置

- Router：`harness-core/router.md`
- 开发全局规则：`harness-core/protocols/development-rules.md`
- Codex 子智能体协议：`harness-core/protocols/codex-subagents.md`
- 开发循环：`harness-core/protocols/development-loop.md`
- Planner：`harness-core/agents/planner.md`
- Developer：`harness-core/agents/developer.md`
- Tester：`harness-core/agents/tester.md`
- 技术方案（阶段 TS）：`harness-core/agents/solution-designer.md`（工作方法：`harness-core/skills/solution-design/SKILL.md`）
- 产品设计：`harness-core/skills/sdd-product-design/SKILL.md`
- Bugfix：`harness-core/skills/sdd-bugfix/SKILL.md`

## 禁止

- 不要维护 `.codex/agents/*.toml` 里的核心流程，只能写入口适配。
- 不要复制 `.cursor/` 或 `.claude/` 的规则当作核心规则。
- 不要把项目内依赖安装交给用户手动执行。

