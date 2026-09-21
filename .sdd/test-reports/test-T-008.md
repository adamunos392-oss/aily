# 测试报告：T-008 F-005 会议室查询功能闭环

**测试时间**：2026-09-21 22:42
**Tester Agent ID**：tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | [AC-F005-01] 用户在对话工作台发送「查询明天下午 3 点以后可用的会议室」或点「查询信息」，中栏展示可用会议室列表，本轮为已回复 | PASS | 新建对话后点「查询信息」；中栏用户句为该问句，助手「明天下午 15:00 以后可用的会议室：」+ 星河 3 号「明天下午 15:00–18:00 空闲」、启航厅「明天下午 15:00–16:30 空闲」。API `POST /turns` `status=replied` `message_type=room_list` |
| 2 | [AC-F005-02] 用户完成会议室查询后，中栏与右栏均不出现写操作确认单或「会议已创建」，事件流为只读查询 | PASS | 中栏无确认卡/同意按钮、无「会议已创建」；过程为改写→意图「查询会议室　只读」→槽位→记忆→路由「只读查询」→原子能力「查询会议室成功」→结果核验→最终「已回复 · 未创建会议」；无 confirmation / risk_permission。运行时 `meetings=0`，本轮未新增 confirmation（库内仅夹具 `cfm-switch-a`） |
| 3 | [AC-F005-03] 当预置无可用会议室时，中栏明确告知无可用结果，不出现已预订或会议已创建文案 | PASS | pytest `monkeypatch` `ToolAdapter.demo_rooms` → `[]`：`text=该时段没有可用会议室。` `rooms=[]`，助手正文不含「已预订/会议已创建」；事件「查询会议室 · 无空闲」「已回复 · 未预订、未创建会议」。默认种子仍为两间会议室 |
| 4 | VITE_USE_MOCK=false 时 turns 请求命中真实后端，页面无 [Mock] 标记 | PASS | `frontend/.env` `VITE_USE_MOCK=false`；场景下拉 disabled；performance 资源含 `POST /api/conversations/conv-1d71569f26a4/turns` 与 `GET .../turns/turn-758ad139ee95`；`document.body` 无 `[Mock]` |
| 5 | 页面布局、配色与全部文案与 `docs/prototypes/01-workbench.html#rooms` 对应 section 一致 | PASS | 中栏标题、房间名、空闲窗口与 `#rooms` 一致；空态 banner 文案与 `#rooms-empty` 一致（pytest）；`.room-grid` / `.room-card` 取值沿用 tokens；壳层沿用 T-001 |

## technicalChecks 验证

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | `python3.12 -m pytest backend/tests/features/f005/ --timeout=120` 通过 | PASS | **4 passed**；全量 `backend/tests` **58 passed** |
| 2 | Typecheck passes | PASS | mypy 68 files Success；`npm run type-check` 通过 |
| 3 | Lint passes | PASS | ruff All checks passed；`npm run lint` 通过 |
| 4 | 样式取值与 design-tokens.md 一致 | PASS | 本任务未改 CSS/tokens；会议室卡片沿用 T-001 已对齐的 `.room-grid` / `.room-card` |
| 5 | VITE_USE_MOCK=false 时不走 mocks 会议室查询分支 | PASS | `turn.ts` `isMockEnabled()` 为 false，XHR 打真实 `/turns` |
| 6 | 查询轮次 confirmations/meetings 无新行；trace 无 confirmation 节点 | PASS | pytest `test_room_query_is_read_only`；浏览器过程无「确认」；live DB `meetings=0` |
| 7 | API 契约 API-F002-01/02 | PASS | 信封 `{code,message,data}`；`room_list` 无 confirmation；GET 快照与 POST 房间列表一致 |

## 环境与规范抽检

- Python 3.12.14；uvicorn `127.0.0.1:8099` 已用当前代码重启（`PYTHONPATH=..:.`）
- 前端 `http://127.0.0.1:5199/`，`VITE_BACKEND_PROXY_TARGET=http://localhost:8099`
- 分层：Route → TurnService → AgentOrchestrator → ReadToolPlugin → ToolService → ToolAdapter
- 测试用独立 tmp 库 `aily-f005.db`，未 drop 运行时库；pytest 后 `meeting_rooms` 仍有星河 3 号 / 启航厅
- 无密钥写入报告

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | 真实编排仍记录改写 / 槽位 / 记忆 / 结果核验，比原型 4 步事件多 | T-005 真实步骤 vs 原型精简 | 按 BR-013 保留真实节点 |
| 2 | 场景条下拉仍有「会议已创建」选项文案（disabled） | T-001 原型场景条 | 非本轮产品中栏/右栏，不纳入 FAIL |
