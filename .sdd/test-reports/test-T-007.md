# 测试报告：T-007 F-002 企业知识问答功能闭环

**测试时间**：2026-09-21 21:41
**Tester Agent ID**：tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | [AC-F002-01] 用户发送「公司的差旅住宿标准是什么？」，看到含职级、城市类型与限额的表格答案，数字可对上引用，本轮为已回复 | PASS | 工作台新建对话发送该问句后中栏表格 P1-P3 一线 ≤800 / 其他 ≤600、P4 及以上一线 ≤1,200；引用《差旅管理制度（2024 版）》第 3.2 条含 800。`POST /turns` `status=replied` `message_type=knowledge_table` |
| 2 | [AC-F002-02] 用户发送预置无依据问句，看到未找到可靠企业知识依据的拒答，无虚构制度与假引用 | PASS | 发送 `KNOWLEDGE_REFUSE_DEMO_QUERY`（公司上市时间表是什么？）后 banner「未找到可靠企业知识依据，无法回答该问题。」+ 原型补充句；无表格。API `status=refused` `citations=[]` |
| 3 | [AC-F002-03] 有据问答后右栏「过程」按时间展示改写、意图、路由到知识、检索、引用核验、最终结果，不出现写操作确认节点 | PASS | 事件含 问题改写 / 意图识别 / 路由到企业知识 / 知识检索 / 引用核验通过 / 最终结果；无「确认」。pytest `test_travel_trace_is_read_only` 断言 nodes 无 confirmation / risk_permission |
| 4 | [AC-F002-04] 「相关来源」文档与片段与中栏引用一致，关键数字不缺失 | PASS | 来源：「1. 《差旅管理制度（2024 版）》第 3.2 条：一线城市 P1-P3 住宿标准不超过 800 元/晚。」与中栏引用同源；拒答轮次来源为空「本轮无知识来源」 |
| 5 | VITE_USE_MOCK=false 时 turns 请求命中真实后端，页面无 [Mock] 标记 | PASS | performance 资源 `POST /api/conversations/{id}/turns` 与 `GET .../turns/{turn_id}`；场景下拉 disabled；`body` 无 `[Mock]` |
| 6 | 页面布局、配色与全部文案与 `#qa-success` / `#qa-refuse` 对应 section 一致 | PASS | 表格表头、限额格式、引用两行、拒答 banner 与补充句与 `01-workbench.html` 一致；壳层沿用 T-001 tokens |

## technicalChecks 验证

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | `python3.12 -m pytest backend/tests/features/f002/ --timeout=120` 通过 | PASS | **8 passed**；全量 `backend/tests` **54 passed** |
| 2 | Typecheck passes | PASS | mypy 63 files Success；`npm run type-check` 通过 |
| 3 | Lint passes | PASS | ruff All checks passed；`npm run lint` 通过 |
| 4 | 样式取值与 design-tokens.md 一致 | PASS | 本任务未改 CSS/tokens |
| 5 | VITE_USE_MOCK=false 时不走 mocks turns 分支 | PASS | `turn.ts` `isMockEnabled()` 为 false，XHR 打真实 `/turns` |
| 6 | 拒答 citations 为空；有据 trace 无 confirmation | PASS | 见上；API 与浏览器一致 |
| 7 | API 契约 API-F002-01/02 | PASS | 空 content 400；对话不存在 404；他人对话 409；GET 快照与 POST 一致 |

## 环境与规范抽检

- Python 3.12.14；uvicorn `127.0.0.1:8099` 已用当前代码重启
- 分层：Route → TurnService → AgentOrchestrator → Plugin → Service → Mock Adapter
- 测试用独立 tmp 库，未 drop 运行时库
- 无密钥写入报告

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | 真实编排仍记录 slot_fill / memory / result_validate，比原型 6 步事件多 | T-005 真实步骤 vs 原型精简 | 按 BR-013 保留真实节点；后续若要对齐原型 6 步需产品确认是否允许过滤展示 |
| 2 | 会议/周报/会议室 turns 已能经同一 POST 跑编排，但确认单落库与 UI 闭环属 T-008/T-009/T-010 | 后续 Feature | 不在本任务验收 |
