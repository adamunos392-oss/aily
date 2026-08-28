# SDD V7_2 — 项目管理型 AI Coding Harness

> Spec-Driven Development V7_2：从“项目内开发规范包”升级为“多项目管理 Harness”，并支持 Codex / Claude Code / Cursor 三端入口。

---

## V7_2 的定位

SDD V7_2 不再默认“当前文件夹就是项目”。它是一个 **项目管理系统**：

1. 先管理项目仓库 `Projects_Repo/`
2. 再选择新建项目 / 克隆项目 / 继续已有项目 / 功能升级 / Bugfix
3. 然后进入单个项目工作区
4. 最后执行产品设计、多 Agent 开发、测试、修复和经验沉淀

一句话：

> V5 是开发规范包，V7_2 是项目管理型、多平台 Agent Harness。

核心原则：

- `harness-core/` 是唯一真相源
- `.codex/`、`.claude/`、`.cursor/` 只做平台适配
- `Projects_Repo/<project-id>/` 只放业务项目状态和代码，不再复制整套平台规则

---

## 目录结构

```text
SDD_V7_2/
├── AGENTS.md                        # Codex 自动入口
├── START.md                         # 非 Cursor 兜底 / 教学说明
├── HARNESS.md                       # Harness 使用规范
├── project-registry.json            # 项目注册表
│
├── harness-core/                    # 唯一真相源：agents / skills / protocols / specification
│   ├── router.md
│   ├── agents/
│   ├── skills/
│   ├── protocols/
│   └── specification/
│
├── .codex/                          # Codex 适配层：subagents TOML + config
│   ├── config.toml
│   └── agents/
│
├── .claude/                         # Claude Code 适配层
│   ├── CLAUDE.md
│   └── agents/
│
├── Projects_Repo/                   # 默认项目仓库，所有项目放这里
│   └── <project-id>/
│
├── .cursor/                         # Cursor 适配层，所有文件只引用 harness-core
│   ├── agents/
│   ├── skills/
│   └── rules/
│
├── templates/
│   ├── project/                     # 新项目初始化模板
│   ├── tasks.json
│   ├── experience.md
│   └── work-log.md
│
├── memory/
│   └── harness-experience.md        # 系统级经验
│
└── pycore/                          # Python 后端框架底座
```

---

## 项目工作区结构

每个项目都在 `Projects_Repo/<project-id>/` 下：

```text
Projects_Repo/<project-id>/
├── AGENTS.md                        # 项目级轻入口，提示返回 Harness 根目录
├── .sdd/                            # 项目状态脑子
│   ├── project.json                 # 项目元信息
│   ├── status.json                  # 当前阶段状态
│   ├── tasks.json                   # 任务状态机
│   ├── experience.md                # 项目级经验
│   ├── work-log.md                  # 工作日志
│   ├── bug_fix/                     # Bugfix 报告
│   └── test-reports/                # Tester 报告
│
├── docs/
│   ├── PRD.md
│   ├── feature-map.md
│   ├── domain-model.md
│   ├── tech-spec.md
│   ├── data-model.md
│   ├── api-contracts.md
│   ├── Plan.md
│   ├── features/
│   │   └── F-xxx-<slug>/
│   │       ├── spec.md
│   │       └── plan.md
│   └── prototypes/
│
├── frontend/ / mobile/
├── backend/
└── ...
```

---

## 工作流总览

```text
Cursor 自动注入 Harness Router
  │
  ├─ 读取 project-registry.json
  │
  ├─ 选择操作
  │   ├─ 新建项目
  │   ├─ 从 GitHub 克隆项目
  │   ├─ 继续已有项目
  │   ├─ 已有项目功能升级
  │   └─ Bugfix
  │
  ├─ 进入 Projects_Repo/<project-id>/
  │
  ├─ 判断项目形态
  │   ├─ Web：可走 sdd-product-design 全流程
  │   └─ 移动端：警告缺少移动端规范，用户确认后继续
  │
  ├─ 判断项目状态
  │   ├─ 缺产品定义 / Feature Spec / 技术方案 / 技术契约 / Plan → 产品设计或要求用户补齐
  │   └─ 文件齐全 → 多 Agent 开发
  │
  └─ Planner → Developer → Tester → Bugfix / Experience
```


## Codex 使用方式

在 Codex 中打开 Harness 根目录后，先读取：

```text
AGENTS.md
.codex/README.md
```

多智能体开发循环由语义路由触发，无命令层，协议本体位于：

```text
harness-core/protocols/development-loop.md
```

`sdd-start` / `sdd-new-project` / `sdd-align` / `sdd-bugfix` 命令已移除，由 Router 直接路由：开发循环走 `harness-core/protocols/development-loop.md`，新建项目走 `scripts/sdd_project.py new`（见 `harness-core/router.md`），Bugfix 走 `harness-core/skills/sdd-bugfix/SKILL.md`。

Codex 子智能体配置：

```text
.codex/agents/planner.toml
.codex/agents/developer.toml
.codex/agents/tester.toml
```

如果当前 Codex 环境不支持自定义 subagent TOML，按 `harness-core/protocols/codex-subagents.md` 在主会话中模拟 Planner / Developer / Tester 的角色边界。

---

## 核心变化

### 1. 所有项目统一放进 `Projects_Repo/`

无论是新建项目，还是从 GitHub 拉下来的项目，都放在：

```text
Projects_Repo/<project-id>/
```

V7_2 不管理任意外部路径，降低教学和使用复杂度。

### 2. `.sdd/` 替代 `.output/` 成为长期项目状态目录

V5 的 `.output/` 更像临时产物目录。V7_2 里：

- `docs/` 存设计文档
- `.sdd/` 存任务、状态、经验、日志、报告

### 3. 三级经验系统

```text
任务经验 → 项目经验 → 系统经验
```

- 任务经验：具体任务/bug 的局部经验
- 项目经验：当前项目长期有效的经验，写入 `.sdd/experience.md`
- 系统经验：跨项目可复用的 Harness 规则，写入 `memory/harness-experience.md`

经验可以上升，但必须带证据和用户确认。

### 4. Web / 移动端分流

- Web 项目：可以走产品设计 Skill，按 `产品定义 → Feature Map/Spec → 原型 → 数据/API 契约 → Feature Plan/全局 Plan` 产出设计材料
- 移动端项目：当前缺少移动端产品设计和开发 rules，必须警告并等待用户确认；用户需自行提供等价的产品定义、功能规格、原型、数据/API 契约和开发计划

### 5. 产品定义与技术契约分层

```text
PRD 产品定义
  → Feature Map
    → Domain Model
      → Feature Spec / Acceptance Criteria
        → UI 原型
          → tech-spec（技术方案：solution-designer 产选型 / 接口形态 / config 键）
            → Data Model / API Contracts
              → Feature Plan / Global Plan
```

- PRD 不提前锁死物理表字段和 API DTO
- Feature 是业务交付、Tester 验收、CI 追踪和用户门禁单位
- 页面、接口、数据库表和组件只是 Feature 的实现载体
- 每个 MVP Feature 必须拥有独立 `spec.md` 和 `plan.md`

---

## 一句话架构

```text
SDD V7_2 Harness
  → Project Registry
    → Projects_Repo/<project-id>
      → docs + .sdd
        → Product Design / Multi-Agent Development / Bugfix
          → Experience Promotion
            → Harness Evolution
```
