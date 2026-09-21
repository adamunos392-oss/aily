# F-002 完成企业知识问答实施计划

## 1. 追踪信息

- Feature：F-002
- Spec：docs/features/F-002-enterprise-knowledge-qa/spec.md
- Spec 版本：1
- 依赖 Feature：F-001
- Data Model：docs/data-model.md 中 conversations、turns、citations、knowledge_entries、trace_events
- API：API-F002-01、API-F002-02
- 原型：docs/prototypes/01-workbench.html（中栏表格/拒答、右栏事件与来源）

## 2. 实现策略

- 前端实现路径：发送消息、知识表格、拒答、引用列表、本轮事件流；不写 Mock 在组件内
- 后端实现路径：turns 路由 → AgentOrchestratorService；Rewrite/Intent/Router/Rag/ResultValidation Plugin；rag_adapter 确定性命中/拒答
- 状态管理：当前 turn 的 TurnResponse 入 Pinia
- 数据持久化：turns、citations、trace_events；知识 seed
- 外部服务：Mock RAG（adapter，可不暴露 HTTP）
- 权限与安全：只读知识；拒答零引用

## 3. 影响范围

| 层级 | 预计模块/目录 | 变更目的 | 禁止影响 |
|---|---|---|---|
| 前端 | `components/MessageThread.vue`、`TracePanel.vue`、`CitationList.vue` | 问答与过程 | 不得画固定流程图；不得出现确认节点于 READ |
| 后端 | `plugins/`、`repositories/mock/rag_adapter.py` | RAG 与拒答 | 不得引入 LangGraph |
| 数据 | knowledge_entries seed | 差旅标准 | 拒答问句不得命中 |

## 4. 内部 Task 候选

| Task 候选 | 类型 | 产出 | 依赖 | 覆盖 AC |
|---|---|---|---|---|
| 编排与 RAG | backend | turns API、Plugin、adapter、单测 | F-001 | AC-F002-01～04 |
| 问答 UI | frontend/integration | 消息/引用/事件 | 编排与 RAG | AC-F002-01～04 |
| Feature 测试 | test | API + E2E | 前后端完成 | 全部 |

> 此表供 Planner 生成 `.sdd/tasks.json`。任务运行状态统一记录在 `.sdd/tasks.json`。

## 5. 开发规范引用

- 规范集：harness-core/specification/default/
- 前端任务：specification/default/frontend/ + shared/
- 后端任务：specification/default/backend/ + shared/ + backend/plugin.md

只引用路径，不复制内容。

## 6. AC → 测试映射

| AC | 验证类型 | 测试层级 | 计划测试路径 | 确定性命令 | CI 门禁 |
|---|---|---|---|---|---|
| AC-F002-01 | auto | API | backend/tests/features/f002/test_travel_standard.py | python3.11 -m pytest backend/tests/features/f002/test_travel_standard.py --timeout=120 | required |
| AC-F002-02 | auto | API | backend/tests/features/f002/test_refuse.py | python3.11 -m pytest backend/tests/features/f002/test_refuse.py --timeout=120 | required |
| AC-F002-03 | auto | API | backend/tests/features/f002/test_trace_read_only.py | python3.11 -m pytest backend/tests/features/f002/test_trace_read_only.py --timeout=120 | required |
| AC-F002-04 | auto | API | backend/tests/features/f002/test_citations.py | python3.11 -m pytest backend/tests/features/f002/test_citations.py --timeout=120 | required |
| AC-F002-01～04 | auto | E2E | e2e/features/f002-knowledge.spec.ts | npx playwright test e2e/features/f002-knowledge.spec.ts | required |

## 7. 外部服务与测试权限

| 服务 | 配置字段 | Tester 权限 | 缺失时策略 | 可否宣称完整通过 |
|---|---|---|---|---|
| Mock RAG | `MOCK_MODE`、`RAG_TOP_K`、`RAG_MIN_SCORE`、`KNOWLEDGE_REFUSE_DEMO_QUERY` | 本地默认 | 场景无法演示，测试失败 | 否（不得编造制度） |

## 8. 风险、迁移与回滚

- 风险：事件流画成固定图导致 READ 出现确认节点
- 数据迁移：seed 知识条目
- 向后兼容：MVP 无历史
- 回滚边界：删库重建

## 9. Definition of Done

- [ ] Spec 中全部 AC 有验证路径
- [ ] 物理数据与 API 契约已引用
- [ ] 内部 Task 候选覆盖完整纵向闭环
- [ ] 自动化测试路径和 CI 门禁明确
- [ ] 手工 / Agent / 外部服务验收没有伪装成自动通过
- [ ] 没有复制 harness-core 开发规范
