# F-004 生成并修改本周周报实施计划

## 1. 追踪信息

- Feature：F-004
- Spec：docs/features/F-004-weekly-report/spec.md
- Spec 版本：1
- 依赖 Feature：F-001
- Data Model：docs/data-model.md 中 conversations、turns、report_drafts、work_messages、trace_events
- API：API-F002-01、API-F004-01
- 原型：docs/prototypes/01-workbench.html（周报草稿与编辑）

## 2. 实现策略

- 前端实现路径：快捷入口生成本周周报、草稿展示与编辑保存
- 后端实现路径：Skill `generate_work_report`；work_message_fetch Tool；MemoryPlugin 只提供模板/语言/篇幅；PATCH report_drafts
- 状态管理：当前草稿 content / is_edited
- 数据持久化：report_drafts；work_messages seed（含闲聊）
- 外部服务：Mock Skill / Tool
- 权限与安全：事实 ⊆ 本轮 Tool 结果；记忆不得注入事实

## 3. 影响范围

| 层级 | 预计模块/目录 | 变更目的 | 禁止影响 |
|---|---|---|---|
| 前端 | `ReportDraftEditor.vue` | 生成与编辑 | 不得把闲聊写入可见事实列表 |
| 后端 | `skill_adapter.py`、`conversations.py` report_drafts | 周报 Skill | 不得用长期记忆补事实 |
| 数据 | work_messages、report_drafts | seed 与草稿 | 无 |

## 4. 内部 Task 候选

| Task 候选 | 类型 | 产出 | 依赖 | 覆盖 AC |
|---|---|---|---|---|
| 周报 Skill 与保存 API | backend | turns 周报链、PATCH draft、单测 | F-001 | AC-F004-01～04 |
| 周报 UI | frontend/integration | 草稿编辑 | 周报 Skill 与保存 API | AC-F004-01～04 |
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
| AC-F004-01 | auto | API | backend/tests/features/f004/test_generate_report.py | python3.11 -m pytest backend/tests/features/f004/test_generate_report.py --timeout=120 | required |
| AC-F004-02 | auto | API | backend/tests/features/f004/test_facts_from_tools.py | python3.11 -m pytest backend/tests/features/f004/test_facts_from_tools.py --timeout=120 | required |
| AC-F004-03 | auto | API | backend/tests/features/f004/test_memory_format_only.py | python3.11 -m pytest backend/tests/features/f004/test_memory_format_only.py --timeout=120 | required |
| AC-F004-04 | auto | API | backend/tests/features/f004/test_edit_draft.py | python3.11 -m pytest backend/tests/features/f004/test_edit_draft.py --timeout=120 | required |
| AC-F004-01～04 | auto | E2E | e2e/features/f004-report.spec.ts | npx playwright test e2e/features/f004-report.spec.ts | required |

## 7. 外部服务与测试权限

| 服务 | 配置字段 | Tester 权限 | 缺失时策略 | 可否宣称完整通过 |
|---|---|---|---|---|
| Mock Skill | `WEEKLY_REPORT_SKILL_ID`、`MOCK_MODE` | 本地默认 | 测试失败 | 否 |

## 8. 风险、迁移与回滚

- 风险：记忆注入本周事实
- 数据迁移：seed 工作消息与闲聊
- 向后兼容：MVP 无历史
- 回滚边界：删库重建

## 9. Definition of Done

- [ ] Spec 中全部 AC 有验证路径
- [ ] 物理数据与 API 契约已引用
- [ ] 内部 Task 候选覆盖完整纵向闭环
- [ ] 自动化测试路径和 CI 门禁明确
- [ ] 手工 / Agent / 外部服务验收没有伪装成自动通过
- [ ] 没有复制 harness-core 开发规范
