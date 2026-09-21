# F-006 评测与 Bad Case 对照（Demo Validation）实施计划

## 1. 追踪信息

- Feature：F-006
- Spec：docs/features/F-006-evaluation-cases/spec.md
- Spec 版本：2
- 依赖 Feature：无产品依赖；对照数据覆盖 S-001～S-007 预置快照
- Data Model：docs/data-model.md 中 evaluation_cases
- API：API-F006-01、API-F006-02；AC-F006-05 无（纯前端）
- 原型：docs/prototypes/demo/evaluation.html；工作台无评测导航见 01-workbench.html

## 2. 实现策略

- 前端实现路径：独立路由 `/demo/evaluation`；横幅「Demo Validation / 非产品功能」；员工工作台导航只有「对话」，禁止调用 evaluation_cases
- 后端实现路径：evaluation_cases 路由 + evaluation_adapter 预置 7 案；回放只读
- 状态管理：仅 Demo 页 store
- 数据持久化：evaluation_cases seed，`EVALUATION_CASE_COUNT_EXPECTED=7`
- 外部服务：Mock Evaluation adapter
- 权限与安全：回放不调用 approve；不写 meetings / knowledge

## 3. 影响范围

| 层级 | 预计模块/目录 | 变更目的 | 禁止影响 |
|---|---|---|---|
| 前端 | `views/demo/EvaluationView.vue`、router | Demo 验证台 | 不得加入员工侧栏 |
| 后端 | `evaluation_cases.py`、`evaluation_adapter.py` | 列表与回放 | 回放不得执行 WRITE Tool |
| 数据 | evaluation_cases | 7 条 seed | 员工 API 不得读此表 |

## 4. 内部 Task 候选

| Task 候选 | 类型 | 产出 | 依赖 | 覆盖 AC |
|---|---|---|---|---|
| 评测只读 API | backend | evaluation_cases 路由、单测 | 基础设施 | AC-F006-01～04 |
| Demo 验证台 UI | frontend/integration | `/demo/evaluation` | 评测只读 API | AC-F006-01～04 |
| 工作台隔离 | frontend | 导航与路由守卫 | 工作台壳 | AC-F006-05 |
| Feature 测试 | test | API + E2E | 前后端完成 | 全部 |

> 此表供 Planner 生成 `.sdd/tasks.json`。任务运行状态统一记录在 `.sdd/tasks.json`。

## 5. 开发规范引用

- 规范集：harness-core/specification/default/
- 前端任务：specification/default/frontend/ + shared/
- 后端任务：specification/default/backend/ + shared/

只引用路径，不复制内容。

## 6. AC → 测试映射

| AC | 验证类型 | 测试层级 | 计划测试路径 | 确定性命令 | CI 门禁 |
|---|---|---|---|---|---|
| AC-F006-01 | auto | API | backend/tests/features/f006/test_list_cases.py | python3.11 -m pytest backend/tests/features/f006/test_list_cases.py --timeout=120 | required |
| AC-F006-02 | auto | API | backend/tests/features/f006/test_case_replay.py | python3.11 -m pytest backend/tests/features/f006/test_case_replay.py --timeout=120 | required |
| AC-F006-03 | auto | API | backend/tests/features/f006/test_replay_no_meeting.py | python3.11 -m pytest backend/tests/features/f006/test_replay_no_meeting.py --timeout=120 | required |
| AC-F006-04 | auto | API | backend/tests/features/f006/test_case_stability.py | python3.11 -m pytest backend/tests/features/f006/test_case_stability.py --timeout=120 | required |
| AC-F006-05 | auto | E2E | e2e/features/f006-workbench-no-eval.spec.ts | npx playwright test e2e/features/f006-workbench-no-eval.spec.ts | required |
| AC-F006-01～04 | auto | E2E | e2e/features/f006-evaluation.spec.ts | npx playwright test e2e/features/f006-evaluation.spec.ts | required |

## 7. 外部服务与测试权限

| 服务 | 配置字段 | Tester 权限 | 缺失时策略 | 可否宣称完整通过 |
|---|---|---|---|---|
| Mock Evaluation | `EVALUATION_CASE_COUNT_EXPECTED` | 本地默认 | 测试失败 | 否 |

## 8. 风险、迁移与回滚

- 风险：评测字段渗入员工工作台
- 数据迁移：seed 7 案
- 向后兼容：MVP 无历史
- 回滚边界：删库重建

## 9. Definition of Done

- [ ] Spec 中全部 AC 有验证路径
- [ ] 物理数据与 API 契约已引用
- [ ] 内部 Task 候选覆盖完整纵向闭环
- [ ] 自动化测试路径和 CI 门禁明确
- [ ] 手工 / Agent / 外部服务验收没有伪装成自动通过
- [ ] 没有复制 harness-core 开发规范
