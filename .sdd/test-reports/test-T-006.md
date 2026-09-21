# 测试报告：T-006 F-001 对话上下文功能闭环

**测试时间**：2026-09-21 21:24
**Tester Agent ID**：tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | [AC-F001-01] 用户在对话工作台点击「新建对话」，中栏为空上下文，不出现其他对话的消息或待确认会议 | PASS | 浏览器点击「新建对话」后场景切到「空对话」，中栏文案为「新对话。从上方功能进入，或直接输入问题。」；`POST /api/conversations` 返回 `turns=[]`、`active_slot_state=null`、`active_confirmation=null`，标题 `新对话` |
| 2 | [AC-F001-02] 用户在对话 A 有待确认单时切换到对话 B，B 不携带 A 的槽位和确认单，也不能用 A 的确认单创建会议 | PASS | `GET /api/conversations/conv-switch-a`：`active_confirmation.confirmation_id=cfm-switch-a`，槽位 `meeting_time=明天下午三点`；`GET .../conv-switch-b`：`active_confirmation=null`，槽位 `meeting_time=周五上午十点`。工作台从 A 切到 B 后中栏仅「公司的差旅住宿标准是什么？」，不含张明会议正文；B 无确认卡/同意按钮，无法用 A 的确认单创建会议。pytest `test_switch_conversation_isolates_slot_and_confirmation` 通过 |
| 3 | [AC-F001-03] 用户查看左侧「最近对话」列表，只看到林小北自己的对话 | PASS | 列表 5 条均为 `mock-linxiaobei`（差旅 / 约张明 / 两条「新对话」/ 会议超时演示）；`conv-foreign`（someone-else）`GET` 为 404「对话不存在」，侧栏无「他人对话」。pytest `test_list_conversations_only_current_user` 通过 |
| 4 | [AC-F001-04] 用户进入工作台，右上角可见「林小北｜产品部」 | PASS | DOM `.identity` 为「林 / 林小北 / 产品部」（与原型两行排版一致）；`GET /api/identity` `display_name=林小北` `department=产品部` `user_id=mock-linxiaobei` |
| 5 | VITE_USE_MOCK=false 时页面请求命中真实后端 /api/identity 与 /api/conversations*，页面无 [Mock] 标记 | PASS | `frontend/.env` 与 `.env.example` 均为 `VITE_USE_MOCK=false`；场景下拉 disabled；performance 资源为 `http://127.0.0.1:5199/api/identity`、`/api/conversations?limit=20`、`/api/conversations/conv-switch-a`、`/api/conversations/conv-switch-b`（经 Vite 代理到 8099）；`document.body` 无 `[Mock]` |
| 6 | 页面布局、配色与全部文案与 `docs/prototypes/01-workbench.html` 对应 section 一致 | PASS | 工作台壳层沿用 T-001 已对齐实现：顶栏 Aily/企业智能助手、搜索占位、侧栏仅「对话」+「新建对话」+「最近对话」、快捷入口文案、空态与输入框/发送与原型一致；本任务未改 tokens/CSS，ProtoSceneBar 仍保留原型「原型场景切换（非产品功能）」文案，Mock 关闭时下拉禁用 |

## technicalChecks 验证

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | `python3.12 -m pytest backend/tests/features/f001/ --timeout=120` 通过 | PASS | `backend/.venv/bin/python -m pytest backend/tests/features/f001 --timeout=60` → **8 passed**；全量 `backend/tests --timeout=120` → **46 passed** |
| 2 | Typecheck passes | PASS | `mypy backend/src backend/tests` → Success, 54 files；`cd frontend && npm run type-check` 通过 |
| 3 | Lint passes | PASS | `ruff check backend/src backend/tests` All checks passed；`cd frontend && npm run lint` 通过 |
| 4 | 样式取值与 docs/prototypes/design-tokens.md 逐项一致 | PASS | 本任务未改样式表/色值；工作台视觉沿用 T-001 已按 tokens 验收的实现 |
| 5 | VITE_USE_MOCK=false 时不走 frontend/src/mocks/* 的 identity/conversations 分支 | PASS | `identity.ts` / `conversation.ts` 以 `isMockEnabled()`（`import.meta.env.VITE_USE_MOCK === "true"`）分路；运行时为 false，XHR 打到 `/api/identity` 与 `/api/conversations*`，未走 mock 函数 |
| 6 | API 契约符合 docs/api-contracts.md API-F001-01～04 | PASS | 信封 `{code,message,data}`；identity 字段与权限数组一致；list 含 `items/total` 与四字段 summary；create 空上下文；详情含 `turns/active_slot_state/active_confirmation`；他人对话 404「对话不存在」；limit 越界由 pytest 覆盖 |

## 环境与规范抽检

- Python：`backend/.venv/bin/python` → 3.12.14
- 后端启动：`cd backend && PYTHONPATH=..:. .venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8099`；`GET /health` 200；旧 PID 23825（无 identity 路由）已替换
- 前端：`cd frontend && npm run dev` → `http://127.0.0.1:5199/`，`VITE_BACKEND_PROXY_TARGET=http://localhost:8099`
- 分层：Route → ConversationService → ConversationRepository；身份来自 config Mock UserContext，不读用户表
- 测试隔离：f001 使用独立 session，未对运行时库 `drop_all`
- 无 `[Mock]` 产品文案；无密钥写入报告

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | Mock 关闭时 `hydrateTurns` 跳过 `GET /turns/{id}`，确认卡/事件流详情要等 turns API | T-007 | 知识问答闭环实现 POST/GET turns 后再渲染 AssistantBubble 完整结构 |
| 2 | 为联调 AC-F001-02 向运行时库写入 `conv-switch-a/b` 与 `conv-foreign` 夹具 | 环境数据 | 仅本地演示数据，不纳入产品种子；勿 `drop_all` 运行时库 |
| 3 | 启动 uvicorn 必须把项目根 `pycore/` 放进 PYTHONPATH（`PYTHONPATH=..:.`） | 启动约定 | 后续任务沿用，勿只设 `PYTHONPATH=.` |
