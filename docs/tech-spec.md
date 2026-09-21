# 技术方案：Aily 企业智能助手

active_project_id: aily  
active_project_path: /Users/lx/Desktop/work/Developer_Helper/Projects_Repo/aily/  
specification: default  
规范集路径: harness-core/specification/default/

---

## 0 方案约束摘要（阶段 TS 锁定）

| 约束项 | 方案决策 |
|---|---|
| 员工侧 MVP Feature | 仅 F-001～F-005；F-006 为 Demo Validation，不计入员工产品 Feature |
| 员工正式导航 | 仅「对话」+ 最近会话；禁止评测字段与评测导航 |
| Demo 验证台 | 独立路由 `/demo/evaluation`；入口为原型场景条或该路由，非员工导航 |
| 身份 | 无登录；Mock UserContext 固定林小北｜产品部 |
| Agent 链路 | Query Rewrite → Intent → Slot/Memory →（WRITE 时 Risk & Permission）→ Router → RAG / Skill / 只读查询 → Result Validation → Response；禁止 Planner / ReAct / Multi-Agent |
| 第一版数据 | 全程 deterministic mock；相同 `(query + conversation_state)` 稳定复现；Mock 经 service / repository / mock adapter，禁止写死在 Vue 组件 |
| Mock Adapter | rewrite、intent、slot、router、rag、tool、skill、evaluation |
| 后端调用链 | Router → PluginRegistry → Plugin → Service（Agent 节点）；Tool 走 pycore Plugin |
| 存储 | SQLite `data/aily.db`（相对 `backend/`）；端口见 env-policy：Agent 5199/8099，用户验收 5175/8003 |

---

## 1 选型清单

> 逐项从 `harness-core/specification/default/backend/tech-stack.md` 与 `frontend/tech-stack.md` 白名单选取，版本写死。

| 层 | 选型 | 版本 | 来源白名单 |
|---|---|---|---|
| Python 运行时 | Python | 3.11+ | backend/tech-stack.md |
| 后端框架 | FastAPI（基于 pycore APIServer） | 0.115.6 | backend/tech-stack.md |
| ASGI 服务器 | uvicorn[standard] | 0.32.1 | backend/tech-stack.md |
| 后端底座 | pycore（PYTHONPATH 引入，禁止 pip 安装） | 0.1.0（Harness 内置） | backend/tech-stack.md |
| 数据校验 | Pydantic | 2.10.4 | backend/tech-stack.md |
| 配置 | pydantic-settings + pycore ConfigManager | 2.7.0 | backend/tech-stack.md |
| ORM | SQLAlchemy[asyncio] | 2.0.36 | backend/tech-stack.md |
| SQLite 驱动 | aiosqlite | 0.20.0 | backend/tech-stack.md |
| HTTP 客户端 | httpx（外部/Mock 服务调用，`trust_env=False`） | 0.28.1 | backend/tech-stack.md + shared/security.md |
| 环境文件 | python-dotenv（仅 ConfigManager 加载 `.env`） | 1.0.1 | backend/tech-stack.md |
| 质量工具 | ruff / mypy / pytest / pytest-asyncio / pytest-timeout | 0.8.4 / 1.14.0 / 8.3.4 / 0.25.0 / 2.3.1 | backend/tech-stack.md |
| 前端框架 | Vue 3（Composition API） | 3.5.13 | frontend/tech-stack.md |
| 语言 | TypeScript | 5.7.2 | frontend/tech-stack.md |
| 构建 | Vite | 6.0.5 | frontend/tech-stack.md |
| Vue 插件 | @vitejs/plugin-vue | 5.2.1 | frontend/tech-stack.md |
| 状态管理 | Pinia | 2.3.0 | frontend/tech-stack.md |
| 前端路由 | Vue Router | 4.5.0 | frontend/tech-stack.md |
| 请求库 | Axios（单一实例，`services/` 封装） | 1.7.9 | frontend/tech-stack.md |
| 数据库 | SQLite | — | backend/tech-stack.md |

**明确不引入（偏航）：** LangGraph、LangChain、dashscope SDK、开放规划框架、全局 AuthMiddleware。

---

## 2 页面/功能矩阵

> 页面清单继承 `docs/prototypes/`（`01-workbench.html`、`demo/evaluation.html`），不增删。

| 页面 | 路由 | Feature / AC | 内容 | 承载功能 | 调用接口 |
|---|---|---|---|---|---|
| 对话工作台 | `/` | F-001 / AC-F001-01～04 | 顶栏身份；左栏「对话」+ 新建 + 最近会话；中栏快捷入口（知识问答/创建会议/生成周报/查询信息/执行任务）+ 消息流 + 输入框；右栏「过程」事件流 +「相关来源」 | 独立对话上下文、身份展示、会话切换 | API-F001-01～04 |
| 对话工作台 | `/` | F-002 / AC-F002-01～04 | 差旅有据表格答案 + 引用；拒答；只读知识链事件流；来源与中栏同源 | 企业知识问答（S-001/S-002） | API-F002-01、API-F002-02 |
| 对话工作台 | `/` | F-003 / AC-F003-01～07 | 澄清/消歧/确认卡/成功/未知/确认作废；写操作事件流含风险权限、确认、核验；执行任务与创建会议同链 | 创建会议 Skill（S-003/S-006/S-007） | API-F002-01、API-F002-02、API-F003-01～03 |
| 对话工作台 | `/` | F-004 / AC-F004-01～04 | 可编辑周报草稿；技能步骤事件流；编辑后保留员工版 | 生成周报 Skill（S-004） | API-F002-01、API-F002-02、API-F004-01 |
| 对话工作台 | `/` | F-005 / AC-F005-01～03 | 会议室列表；只读查询事件流；无确认卡 | 只读会议室查询（S-005） | API-F002-01、API-F002-02 |
| 对话工作台 | `/` | F-006 / AC-F006-05 | 左侧无评测导航；主流程无预期/实际路由、Pass/Fail、Bad Case、案例列表 | 员工侧禁止评测入口（约束验收） | API-F001-01～04（无 evaluation 接口消费） |
| Demo 验证台（非产品） | `/demo/evaluation` | F-006 / AC-F006-01～04 | 横幅「Demo Validation / 非产品功能」；案例表；路由对照；事件流回放；返回工作台链接（非员工导航项） | Demo Validation Harness（S-008） | API-F006-01、API-F006-02 |

**前端路由文件：** `frontend/src/router/index.ts`  
- `/` → `pages/WorkbenchPage.vue`（对应 `01-workbench.html`）  
- `/demo/evaluation` → `pages/DemoEvaluationPage.vue`（对应 `demo/evaluation.html`；`meta.isDemoValidation=true`，不挂载员工侧栏）

**原型场景条：** 仅开发/演示切换 UI 状态，不新增业务路由；可链至 `/demo/evaluation`。

---

## 3 接口设计

> 响应统一 pycore 信封：`{"code": "<OK|错误码>", "message": "<人类可读>", "data": <T|null>}`（见 `specification/default/backend/api-design.md`）。  
> 路由文件：`backend/src/api/routes/<资源复数>.py`；URL 前缀 `/api/<资源复数>`。  
> 资源词来源：PRD 名词实体——`identity`（演示身份）、`conversations`（对话）、`confirmations`（确认单，回指 conversation/turn）、`evaluation_cases`（Demo 专用）。

### 3.0 共享领域类型（Pydantic ↔ TypeScript 对齐）

方案层核心 Type（`backend/src/models/agent/` + `frontend/src/types/agent.ts` 照抄）：

```python
# --- 查询上下文 ---
class QueryContext(BaseModel):
    conversation_id: str
    turn_id: str
    raw_query: str
    entry_source: Literal["manual", "shortcut_knowledge", "shortcut_meeting", "shortcut_report", "shortcut_query", "shortcut_task"]
    user_id: str  # 固定 mock 用户 ID

class RewriteResult(BaseModel):
    raw_query: str
    rewritten_query: str

class IntentResult(BaseModel):
    intent: Literal["enterprise_knowledge", "create_meeting", "generate_work_report", "query_meeting_rooms", "unknown"]
    operation_type: Literal["READ", "WRITE"]
    confidence: float  # mock 固定 1.0

class SlotState(BaseModel):
    slots: dict[str, str | list[str] | None]  # 如 meeting_time, attendees, topic, duration_minutes, meeting_type, selected_person_id
    missing_required: list[str]
    is_complete: bool

class MemoryState(BaseModel):
    template_style: Literal["bullet_list"]  # 林小北稳定偏好
    language: Literal["zh-CN"]
    length: Literal["concise"]
    # 仅模板/语言/篇幅；不得注入本周工作事实

class RouteDecision(BaseModel):
    route_type: Literal["RAG", "SKILL", "READ_TOOL"]
    target: str  # 如 enterprise_knowledge | create_meeting | generate_work_report | query_meeting_rooms
    display_route: str  # 事件流与 Demo 对照展示用，如「企业知识」「技能 create_meeting」

class Citation(BaseModel):
    document_title: str
    section: str
    excerpt: str
    knowledge_entry_id: str

class ToolDefinition(BaseModel):
    tool_id: Literal["people_lookup", "calendar_check", "meeting_create", "work_message_fetch", "meeting_room_query"]
    name: str
    operation_type: Literal["READ", "WRITE"]

class ToolCall(BaseModel):
    tool_id: str
    arguments: dict[str, str | int | list[str]]
    call_id: str

class ToolResult(BaseModel):
    call_id: str
    tool_id: str
    status: Literal["success", "failure", "timeout", "unknown"]
    payload: dict | None
    error_message: str | None

class SkillDefinition(BaseModel):
    skill_id: Literal["create_meeting", "generate_work_report"]
    name: str
    description: str
    orchestrated_tools: list[str]

class TraceEvent(BaseModel):
    event_id: str
    turn_id: str
    sequence: int
    occurred_at: datetime
    node: Literal[
        "query_rewrite", "intent", "slot_fill", "memory", "risk_permission",
        "router", "rag_retrieve", "citation_validate", "skill", "tool_call",
        "confirmation", "result_validate", "final"
    ]
    title_zh: str
    summary: str
    payload: dict  # 节点关键字段，如 rewritten_query / intent / slots / route / hit_count

class EvaluationCase(BaseModel):
    case_id: str
    name: str
    scene_id: Literal["S-001", "S-002", "S-003", "S-004", "S-005", "S-006", "S-007"]
    query: str
    expected_route: str
    actual_route: str
    passed: bool
    bad_case_category: Literal["none", "no_evidence_refusal", "timeout_unknown", "confirmation_invalidated"]
    trace_events: list[TraceEvent]
```

**Agent 编排（Service 层，非开放规划）：**  
`AgentOrchestratorService` 按固定顺序调用 PluginRegistry 注册插件：`RewritePlugin` → `IntentPlugin` → `SlotPlugin` → `MemoryPlugin` →（WRITE 时 `RiskPermissionPlugin`）→ `RouterPlugin` → 分支（`RagPlugin` / `SkillPlugin` / `ReadToolPlugin`）→ `ResultValidationPlugin` → 组装 `TurnResponse`。每步只追加真实发生的 `TraceEvent`。

**Mock Adapter 落位（`backend/src/repositories/mock/`）：**

| Adapter | 职责 |
|---|---|
| `rewrite_adapter.py` | deterministic 改写 |
| `intent_adapter.py` | 意图 + operation_type |
| `slot_adapter.py` | 槽位提取/补全/关键槽变更检测 |
| `router_adapter.py` | RouteDecision |
| `rag_adapter.py` | 知识召回 + Citation |
| `tool_adapter.py` | People/Calendar/Meeting/WorkMessage/MeetingRoom 原子 Tool |
| `skill_adapter.py` | create_meeting / generate_work_report 固定编排 |
| `evaluation_adapter.py` | 预置 EvaluationCase 与对照结果 |

---

### 3.1 API-F001-01 获取演示身份：GET /api/identity

- 来源 Feature：F-001（覆盖 AC：AC-F001-04）
- 路由文件：`backend/src/api/routes/identity.py`
- 请求模型：无
- 响应模型：`IdentityResponse`（经 `success_response` 包装）
  - `user_id: str` — 固定 `"mock-linxiaobei"`
  - `display_name: str` — `"林小北"`
  - `department: str` — `"产品部"`
  - `permissions: list[Literal["conversation:read", "conversation:write", "knowledge:read"]]` — 固定列表
- 错误码：`INTERNAL_ERROR`

---

### 3.2 API-F001-02 列出最近对话：GET /api/conversations

- 来源 Feature：F-001（覆盖 AC：AC-F001-03）
- 路由文件：`backend/src/api/routes/conversations.py`
- 查询参数：
  - `limit: int = Field(default=..., ge=1, le=100)` — 默认取自 config `CONVERSATION_LIST_LIMIT`
- 响应模型：`ConversationListResponse`
  - `items: list[ConversationSummary]`
    - `conversation_id: str`
    - `title: str`
    - `updated_at: datetime`
    - `preview: str | None`
  - `total: int`
- 错误码：`VALIDATION_ERROR`

---

### 3.3 API-F001-03 新建对话：POST /api/conversations

- 来源 Feature：F-001（覆盖 AC：AC-F001-01）
- 路由文件：`backend/src/api/routes/conversations.py`
- 请求模型：`ConversationCreateRequest`
  - `title: str | None = None` — 可选；缺省由首条用户消息生成
- 响应模型：`ConversationDetailResponse`
  - `conversation_id: str`
  - `title: str`
  - `created_at: datetime`
  - `turns: list[TurnSummary]` — 新建为空列表 `[]`
  - `active_confirmation: None` — 新对话无确认单
  - `slot_state: SlotState | None` — 新对话为 `None` 或空槽
- 错误码：`VALIDATION_ERROR`、`INTERNAL_ERROR`

---

### 3.4 API-F001-04 获取对话详情：GET /api/conversations/{conversation_id}

- 来源 Feature：F-001（覆盖 AC：AC-F001-02）
- 路由文件：`backend/src/api/routes/conversations.py`
- 路径参数：`conversation_id: str`
- 响应模型：`ConversationDetailResponse`
  - `conversation_id: str`
  - `title: str`
  - `created_at: datetime`
  - `updated_at: datetime`
  - `turns: list[TurnSummary]`
    - `turn_id: str`
    - `role: Literal["user", "assistant"]`
    - `content: str`
    - `status: Literal["processing", "replied", "clarifying", "awaiting_confirmation", "unknown", "refused"]`
    - `created_at: datetime`
  - `active_slot_state: SlotState | None` — 仅当前对话槽位；切换对话时不串
  - `active_confirmation: ConfirmationSummary | None` — 当前未作废的待确认单；切换对话时为 `None`
- 错误码：`NOT_FOUND`（非本身份对话）、`INTERNAL_ERROR`

---

### 3.5 API-F002-01 发起一轮提问：POST /api/conversations/{conversation_id}/turns

- 来源 Feature：F-002 / F-003 / F-004 / F-005（覆盖 AC：AC-F002-01～04、AC-F003-01～07、AC-F004-01～03、AC-F005-01～03）
- 路由文件：`backend/src/api/routes/conversations.py`（动作归入 conversations 资源）
- 请求模型：`TurnCreateRequest`
  - `content: str` — 必填，员工输入或快捷入口预置问句
  - `entry_source: Literal["manual", "shortcut_knowledge", "shortcut_meeting", "shortcut_report", "shortcut_query", "shortcut_task"] = "manual"`
  - `choice_id: str | None = None` — 消歧/澄清选项 ID（如 `"person:zhangming-product"`）
  - `client_turn_key: str | None = None` — 幂等键，可选
- 响应模型：`TurnResponse`
  - `turn_id: str`
  - `conversation_id: str`
  - `status: Literal["processing", "replied", "clarifying", "awaiting_confirmation", "unknown", "refused"]`
  - `user_message: str`
  - `assistant_message: AssistantMessage` — 多态：
    - `message_type: Literal["text", "knowledge_table", "refusal", "clarification", "disambiguation", "confirmation", "meeting_success", "meeting_unknown", "report_draft", "room_list", "empty"]`
    - `text: str | None`
    - `table_rows: list[KnowledgeTableRow] | None` — `{level, city_type, limit_cny}`
    - `choices: list[ChoiceOption] | None` — `{choice_id, label}`
    - `confirmation: ConfirmationSummary | None`
    - `report_draft: ReportDraft | None` — `{draft_id, skill_name, content, is_edited}`
    - `rooms: list[MeetingRoomItem] | None` — `{room_name, available_from, available_to}`
  - `citations: list[Citation]` — 有据问答时有值；拒答为空列表
  - `route_decision: RouteDecision`
  - `trace_events: list[TraceEvent]` — **本轮**完整事件流，按 `sequence` 排序
  - `intent: IntentResult`
  - `slot_state: SlotState | None`
- 业务语义（Mock deterministic）：
  - **S-001** 问句「公司的差旅住宿标准是什么？」→ RAG 命中 → 表格 + 引用 → `status=replied`；事件流无写确认节点
  - **S-002** 预置无依据问句（config `KNOWLEDGE_REFUSE_DEMO_QUERY`）→ `status=refused`，无 citations
  - **S-003** 创建会议链 → 缺槽 `clarifying`；同名 `disambiguation`；槽齐 `awaiting_confirmation`；确认后成功 `replied` + meeting_success
  - **S-004** 「帮我生成本周周报」→ Skill generate_work_report → report_draft
  - **S-005** 「查询明天下午 3 点以后可用的会议室」→ READ_TOOL → room_list；无 confirmation
  - **S-006** 对话 ID = config `MEETING_TIMEOUT_DEMO_CONVERSATION_ID` 且已确认 → Tool timeout → `status=unknown`；assistant 不得含「会议已创建」
  - **S-007** 已确认后修改 `meeting_time` 槽 → 旧 confirmation `invalidated` → 新 confirmation `pending`
  - **执行任务**（`entry_source=shortcut_task`）与创建会议同一 `intent=create_meeting` 链
- 错误码：`NOT_FOUND`、`VALIDATION_ERROR`、`CONFLICT`（对话不属于当前身份）

---

### 3.6 API-F002-02 获取单轮详情（含 Trace / 来源）：GET /api/conversations/{conversation_id}/turns/{turn_id}

- 来源 Feature：F-002 / F-003 / F-004 / F-005（覆盖 AC：AC-F002-03、AC-F002-04、AC-F003-04～06、AC-F005-02）
- 路由文件：`backend/src/api/routes/conversations.py`
- 响应模型：`TurnResponse`（同 API-F002-01）
- 错误码：`NOT_FOUND`

---

### 3.7 API-F003-01 同意确认单：POST /api/conversations/{conversation_id}/confirmations/{confirmation_id}/approve

- 来源 Feature：F-003（覆盖 AC：AC-F003-01、AC-F003-04、AC-F003-06、AC-F003-07）
- 路由文件：`backend/src/api/routes/confirmations.py`
- 路径参数：`conversation_id: str`、`confirmation_id: str`
- 请求模型：`ConfirmationApproveRequest`
  - `turn_id: str` — 必填，回指发起确认的 turn
- 响应模型：`TurnResponse` — 执行 create_meeting Skill 原子 Tool 链；成功则 meeting_success；超时则 unknown（禁止成功文案）
- 业务语义：
  - 确认单状态必须为 `pending` 且未作废（BR-005）
  - 已作废确认单 → `CONFLICT`，message 说明须重新确认
  - 超时场景 → `status=unknown`，trace 含 `tool_call(timeout)` + `result_validate(unknown)`
- 错误码：`NOT_FOUND`、`CONFLICT`（已作废/已取消/已同意）、`VALIDATION_ERROR`

---

### 3.8 API-F003-02 取消确认单：POST /api/conversations/{conversation_id}/confirmations/{confirmation_id}/cancel

- 来源 Feature：F-003（覆盖 AC：AC-F003-04）
- 路由文件：`backend/src/api/routes/confirmations.py`
- 请求模型：`ConfirmationCancelRequest`
  - `turn_id: str`
  - `reason: str | None = None`
- 响应模型：`TurnResponse` — `status=replied`，assistant 说明已取消，不创建会议
- 错误码：`NOT_FOUND`、`CONFLICT`

---

### 3.9 API-F003-03 更新关键槽位（触发确认作废）：PATCH /api/conversations/{conversation_id}/turns/{turn_id}/slots

- 来源 Feature：F-003（覆盖 AC：AC-F003-05）
- 路由文件：`backend/src/api/routes/conversations.py`
- 请求模型：`SlotUpdateRequest`
  - `updates: dict[str, str]` — 至少支持 `meeting_time`（关键槽，BR-006）
- 响应模型：`TurnResponse`
  - 旧 `ConfirmationSummary.status` → `invalidated`
  - 新 `ConfirmationSummary` → `pending`，摘要反映新槽位
  - trace 含 `confirmation(invalidated)` 与新 `confirmation(pending)`
- 错误码：`NOT_FOUND`、`VALIDATION_ERROR`、`CONFLICT`（非 create_meeting 轮次）

---

### 3.10 API-F004-01 保存周报员工编辑版：PATCH /api/conversations/{conversation_id}/turns/{turn_id}/report_drafts/{draft_id}

- 来源 Feature：F-004（覆盖 AC：AC-F004-04）
- 路由文件：`backend/src/api/routes/conversations.py`
- 请求模型：`ReportDraftUpdateRequest`
  - `content: str` — 员工编辑后全文
- 响应模型：`ReportDraftResponse`
  - `draft_id: str`
  - `turn_id: str`
  - `content: str`
  - `is_edited: bool` — 固定 `true`
  - `updated_at: datetime`
- 错误码：`NOT_FOUND`、`VALIDATION_ERROR`

---

### 3.11 API-F006-01 列出评测案例（Demo 专用）：GET /api/evaluation_cases

- 来源 Feature：F-006（覆盖 AC：AC-F006-01、AC-F006-04）
- 路由文件：`backend/src/api/routes/evaluation_cases.py`
- 说明：**仅 Demo 验证台 `/demo/evaluation` 消费**；员工工作台页面矩阵不得调用
- 响应模型：`EvaluationCaseListResponse`
  - `items: list[EvaluationCaseSummary]`
    - `case_id: str`
    - `name: str`
    - `expected_route: str`
    - `actual_route: str`
    - `passed: bool`
    - `bad_case_category: Literal["none", "no_evidence_refusal", "timeout_unknown", "confirmation_invalidated"]`
  - `total: int` — 固定 7（覆盖 S-001～S-007 主链）
- 错误码：`INTERNAL_ERROR`

**预置案例（deterministic，与原型一致）：**

| case_id | name | expected_route | bad_case_category |
|---|---|---|---|
| `eval-qa-travel` | 差旅住宿标准 | 企业知识 | none |
| `eval-qa-refuse` | 无依据问句拒答 | 企业知识-拒答 | no_evidence_refusal |
| `eval-meeting-success` | 创建项目复盘会 | 技能 create_meeting | none |
| `eval-meeting-timeout` | 创建会议超时 | 技能 create_meeting → 未知 | timeout_unknown |
| `eval-meeting-stale` | 改时间后重确认 | 确认作废后重确认 | confirmation_invalidated |
| `eval-report` | 生成本周周报 | 技能 generate_work_report | none |
| `eval-rooms` | 查询可用会议室 | 只读查询 | none |

---

### 3.12 API-F006-02 获取评测案例详情与事件回放：GET /api/evaluation_cases/{case_id}

- 来源 Feature：F-006（覆盖 AC：AC-F006-02、AC-F006-03）
- 路由文件：`backend/src/api/routes/evaluation_cases.py`
- 响应模型：`EvaluationCaseDetailResponse`
  - `case: EvaluationCase` — 含完整 `trace_events`
  - `route_comparison: RouteComparison`
    - `expected_route: str`
    - `actual_route: str`
    - `passed: bool`
  - `replay_note: str` — 固定 `"只读回放，不创建会议、不写入企业知识"`
- 业务语义：回放不触发 API-F003-01；超时案例 trace 不得含「会议已创建」节点
- 错误码：`NOT_FOUND`

---

### 3.13 共享子模型补全

```python
class ConfirmationSummary(BaseModel):
    confirmation_id: str
    turn_id: str
    status: Literal["pending", "approved", "cancelled", "invalidated"]
    meeting_time: str
    attendees: list[str]
    topic: str
    duration_minutes: int
    meeting_type: Literal["online", "offline"]
    slot_snapshot_hash: str  # 槽位快照指纹；变更即作废

class ChoiceOption(BaseModel):
    choice_id: str
    label: str

class ReportDraft(BaseModel):
    draft_id: str
    skill_name: str  # 「生成工作周报」
    content: str
    is_edited: bool

class MeetingRoomItem(BaseModel):
    room_name: str
    available_from: str  # ISO datetime
    available_to: str

class KnowledgeTableRow(BaseModel):
    level: str
    city_type: str
    limit_cny: int
```

---

## 4 config 键清单

> 单一权威源；§2/§3/§5 出现的数值均在此登记。`.env` 策略与端口见 `specification/default/shared/env-policy.md`。

| 键名 | 默认值 | 说明 | 使用处 |
|---|---|---|---|
| `DATABASE_PATH` | `data/aily.db` | SQLite 文件（相对 `backend/`） | db/session.py |
| `UPLOAD_DIR` | `data/uploads` | 持久化目录（MVP 预留） | config |
| `HOST` | `127.0.0.1` | 后端绑定地址 | main.py / APIServer |
| `PORT` | `8099` | Agent 开发后端端口 | main.py / uvicorn |
| `DEBUG` | `true` | 调试模式 | AppSettings |
| `SECRET_KEY` | （`.env` 必填，占位 `change-me-local-only`） | pycore 模板必需；MVP 无登录 | AppSettings |
| `CORS_ORIGINS` | `http://localhost:5199,http://127.0.0.1:5199,http://localhost:5175,http://127.0.0.1:5175` | 前端来源 | APIServer |
| `MOCK_MODE` | `true` | 全程 Mock 开关 | AgentOrchestratorService |
| `MOCK_MODEL_NAME` | `aily-mock-v1` | Mock「模型」名称（事件流展示） | RewritePlugin / SkillPlugin |
| `MOCK_DETERMINISTIC_SEED` | `42` | 相同输入稳定复现 | 全部 mock adapter |
| `MOCK_USER_ID` | `mock-linxiaobei` | 演示身份 ID | deps.get_current_user |
| `MOCK_USER_DISPLAY_NAME` | `林小北` | 展示名 | identity 路由 |
| `MOCK_USER_DEPARTMENT` | `产品部` | 部门 | identity 路由 |
| `RAG_TOP_K` | `5` | 知识召回条数 | rag_adapter |
| `RAG_MIN_SCORE` | `0.75` | 引用核验最低分 | ResultValidationPlugin |
| `KNOWLEDGE_REFUSE_DEMO_QUERY` | `公司上市时间表是什么？` | S-002 拒答演示问句 | intent_adapter / rag_adapter |
| `MEETING_DEFAULT_DURATION_MINUTES` | `60` | 默认会议时长 | slot_adapter / skill_adapter |
| `MEETING_DEFAULT_TYPE` | `online` | 默认会议类型 | slot_adapter |
| `MEETING_DISAMBIGUATION_PERSON_NAME` | `张明` | 消歧演示名 | slot_adapter |
| `MEETING_TIMEOUT_DEMO_CONVERSATION_ID` | `conv-demo-meeting-timeout` | S-006 可重复进入的对话 ID | tool_adapter |
| `TOOL_TIMEOUT_SECONDS` | `30` | 原子 Tool 超时（S-006） | tool_adapter |
| `CONFIRMATION_EXECUTION_WAIT_SECONDS` | `30` | 写操作结果等待上限（BR-007） | ResultValidationPlugin |
| `MEETING_ROOM_QUERY_AFTER_HOUR` | `15` | 会议室查询「下午 3 点以后」 | tool_adapter |
| `MEETING_ROOM_QUERY_DEMO_DATE_OFFSET_DAYS` | `1` | 「明天」偏移天数 | tool_adapter |
| `CONVERSATION_LIST_LIMIT` | `20` | 最近会话列表上限 | conversations 路由 |
| `HTTP_CLIENT_TIMEOUT_SECONDS` | `30` | httpx 超时 | mock/外部 HTTP |
| `TRACE_EVENT_DETAIL_MAX_CHARS` | `500` | 事件 payload 摘要截断 | TraceEvent 组装 |
| `WEEKLY_REPORT_SKILL_ID` | `generate_work_report` | 周报 Skill ID | skill_adapter |
| `CREATE_MEETING_SKILL_ID` | `create_meeting` | 创建会议 Skill ID | skill_adapter |
| `EVALUATION_CASE_COUNT_EXPECTED` | `7` | 验证台案例数验收 | evaluation_adapter |
| `AGENT_FRONTEND_PORT` | `5199` | Agent 前端端口（文档/启动脚本） | vite / 文档 |
| `USER_ACCEPTANCE_FRONTEND_PORT` | `5175` | 用户验收前端端口 | vite / 文档 |
| `USER_ACCEPTANCE_BACKEND_PORT` | `8003` | 用户验收后端端口 | 启动脚本 |
| `VITE_API_BASE_URL` | `/api` | 前端 API 基址（`frontend/.env`） | services/api.ts |
| `VITE_BACKEND_PROXY_TARGET` | `http://127.0.0.1:8099` | Vite 代理目标 | vite.config.ts |
| `AXIOS_TIMEOUT_MS` | `10000` | 前端 HTTP 超时（`frontend/.env`） | services/api.ts |

---

## 5 外部服务规格（写死）

MVP **不接真实 LLM / 飞书 / Aily 后台**；以下为 Mock 内部服务规格（进程内 adapter 实现，URL 供阶段 C 契约与后续替换对齐）。

| 服务 | URL | 模型/字段 | 用途 | 额度来源 |
|---|---|---|---|---|
| Mock Rewrite 服务 | `http://127.0.0.1:8099/internal/mock/rewrite` | 请求：`{raw_query, conversation_id}`；响应：`{rewritten_query}` | 问题改写 | 无 |
| Mock Intent 服务 | `http://127.0.0.1:8099/internal/mock/intent` | 请求：`{rewritten_query, entry_source}`；响应：`{intent, operation_type}` | 意图识别 | 无 |
| Mock Slot 服务 | `http://127.0.0.1:8099/internal/mock/slots` | 请求：`{rewritten_query, conversation_state}`；响应：`SlotState` | 槽位/Memory 读取 | 无 |
| Mock Router 服务 | `http://127.0.0.1:8099/internal/mock/router` | 请求：`{intent}`；响应：`RouteDecision` | 路由 | 无 |
| Mock RAG 服务 | `http://127.0.0.1:8099/internal/mock/rag` | 请求：`{query, top_k}`；响应：`{hits: Citation[], hit_count}` | 企业知识检索 | 无 |
| Mock Tool 服务 | `http://127.0.0.1:8099/internal/mock/tools/{tool_id}` | 请求：`ToolCall`；响应：`ToolResult`；`tool_id` ∈ people_lookup/calendar_check/meeting_create/work_message_fetch/meeting_room_query | 原子 Tool | 无 |
| Mock Skill 服务 | `http://127.0.0.1:8099/internal/mock/skills/{skill_id}` | 请求：`{slot_state, memory_state}`；响应：`{tool_calls[], draft?}` | Skill 编排 | 无 |
| Mock Evaluation 服务 | `http://127.0.0.1:8099/internal/mock/evaluation/cases` | 响应：`EvaluationCase[]` | Demo 验证台 | 无 |

**实现说明：** MVP 阶段上述 URL 可不暴露 HTTP 路由，由 `repositories/mock/*_adapter.py` 直接实现同等字段契约；Plugin 经 Service 调用 Adapter，保持可替换性。禁止引入 LangGraph/LangChain。

---

## 6 风险清单

| 风险 | 影响 | 应对 |
|---|---|---|
| Mock 与 Vue 组件耦合 | 无法 stable 复现 S-001～S-008 | Mock 仅经 repository/adapter；前端只消费 API 信封 |
| 事件流渲染成固定流程图 | READ 场景出现虚假确认节点 | Trace 只追加真实 `TraceEvent`；UI 按时间线渲染 |
| 超时与确认作废共用不可重置对话 | S-006/S-007 无法演示 | 预置 `MEETING_TIMEOUT_DEMO_CONVERSATION_ID` + 槽位变更 API |
| 评测字段渗入员工工作台 | 违反 BR-016 | 路由隔离；evaluation_cases 接口仅 Demo 页调用；AC-F006-05 单列验收 |
| 确认单跨对话串用 | 违反 BR-015/BR-006 | `ConversationDetail.active_confirmation` 按 conversation_id 隔离 |
| 真模型接入导致路由漂移 | 演示不稳定 | `MOCK_MODE=true` 为验收默认；真模型仅未来显式开关，非 MVP 依赖 |
| SQLite 相对路径解析错误 | 启动失败 | 按 tech-stack 规范转绝对路径并 `mkdir` 父目录 |

---

## 7 后端模块落位（Planner 参考，非本阶段代码）

```
backend/src/
├── api/routes/
│   ├── identity.py
│   ├── conversations.py      # turns / slots / report_drafts 动作
│   ├── confirmations.py
│   └── evaluation_cases.py   # Demo 专用
├── api/deps.py                 # get_current_user → Mock UserContext
├── plugins/                    # Agent 节点 Plugin
├── services/
│   ├── agent_orchestrator.py
│   └── conversation_service.py
├── repositories/
│   ├── conversation_repository.py
│   └── mock/                   # 8 个 adapter
└── models/agent/               # §3.0 类型
```

**Plugin 注册（main.py startup）：** RewritePlugin、IntentPlugin、SlotPlugin、MemoryPlugin、RiskPermissionPlugin、RouterPlugin、RagPlugin、SkillPlugin、ReadToolPlugin、ResultValidationPlugin。

---

## 8 自检记录（落盘前）

| 检查项 | 结果 |
|---|---|
| 零 magic number | §2/§3/§5 数值均已映射 §4 config 键 |
| 选型在白名单内 | 未引入 LangGraph/LangChain/dashscope |
| 追踪完整 | 页面矩阵覆盖 F-001～F-006 全部 AC；接口均带 API 编号与 Feature |
| 零追问 | 页面仅 2 个；资源词已推导；Mock/端口/DB/Agent 链/类型均已写死 |
