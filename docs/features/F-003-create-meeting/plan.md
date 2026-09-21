# F-003 用 Skill 创建会议实施计划

## 1. 追踪信息

- Feature：F-003
- Spec：docs/features/F-003-create-meeting/spec.md
- Spec 版本：1
- 依赖 Feature：F-001
- Data Model：docs/data-model.md 中 conversations、turns、confirmations、people、meetings、trace_events
- API：API-F002-01、API-F002-02、API-F003-01、API-F003-02、API-F003-03
- 原型：docs/prototypes/01-workbench.html（澄清、消歧、确认卡、未知）

## 2. 实现策略

- 前端实现路径：澄清/消歧选项、确认卡同意取消、关键时间修改、成功/未知结果；WRITE 展示风险权限、确认、核验对应事件
- 后端实现路径：Slot/RiskPermission/Skill Plugin；skill_adapter 固定编排 people_lookup → calendar_check → meeting_create；超时对话 ID 走 timeout
- 状态管理：当前对话 pending confirmation 与 slot_state
- 数据持久化：confirmations、meetings、people seed
- 外部服务：Mock Tool / Skill adapter
- 权限与安全：未 pending 禁止创建会议；作废确认返回 CONFLICT

## 3. 影响范围

| 层级 | 预计模块/目录 | 变更目的 | 禁止影响 |
|---|---|---|---|
| 前端 | `ConfirmationCard.vue`、`ChoiceList.vue` | 写操作确认 | 不得在 READ 轮展示确认卡 |
| 后端 | `confirmations.py`、`skill_adapter.py`、`tool_adapter.py`、`slot_adapter.py` | Skill 链与确认 | 禁止开放规划/ReAct |
| 数据 | confirmations、meetings、people | 状态机 | 超时路径不得插入 meetings |

## 4. 内部 Task 候选

| Task 候选 | 类型 | 产出 | 依赖 | 覆盖 AC |
|---|---|---|---|---|
| 槽位/确认/Skill API | backend | turns 会议链、approve/cancel/slots、单测 | F-001 | AC-F003-01～07 |
| 会议确认 UI | frontend/integration | 澄清消歧确认未知 | 槽位/确认/Skill API | AC-F003-01～07 |
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
| AC-F003-01 | auto | API | backend/tests/features/f003/test_meeting_success.py | python3.11 -m pytest backend/tests/features/f003/test_meeting_success.py --timeout=120 | required |
| AC-F003-02 | auto | API | backend/tests/features/f003/test_clarify.py | python3.11 -m pytest backend/tests/features/f003/test_clarify.py --timeout=120 | required |
| AC-F003-03 | auto | API | backend/tests/features/f003/test_disambiguation.py | python3.11 -m pytest backend/tests/features/f003/test_disambiguation.py --timeout=120 | required |
| AC-F003-04 | auto | API | backend/tests/features/f003/test_no_create_without_confirm.py | python3.11 -m pytest backend/tests/features/f003/test_no_create_without_confirm.py --timeout=120 | required |
| AC-F003-05 | auto | API | backend/tests/features/f003/test_stale_confirmation.py | python3.11 -m pytest backend/tests/features/f003/test_stale_confirmation.py --timeout=120 | required |
| AC-F003-06 | auto | API | backend/tests/features/f003/test_timeout_unknown.py | python3.11 -m pytest backend/tests/features/f003/test_timeout_unknown.py --timeout=120 | required |
| AC-F003-07 | auto | API | backend/tests/features/f003/test_shortcut_task.py | python3.11 -m pytest backend/tests/features/f003/test_shortcut_task.py --timeout=120 | required |
| AC-F003-01～07 | auto | E2E | e2e/features/f003-meeting.spec.ts | npx playwright test e2e/features/f003-meeting.spec.ts | required |

## 7. 外部服务与测试权限

| 服务 | 配置字段 | Tester 权限 | 缺失时策略 | 可否宣称完整通过 |
|---|---|---|---|---|
| Mock Tool/Skill | `MOCK_MODE`、`CREATE_MEETING_SKILL_ID`、`MEETING_TIMEOUT_DEMO_CONVERSATION_ID`、`TOOL_TIMEOUT_SECONDS` | 本地默认 | 测试失败 | 否（不得把超时显示为已创建） |

## 8. 风险、迁移与回滚

- 风险：S-006 与 S-007 共用不可重置对话
- 数据迁移：seed 两名张明；seed 超时演示对话
- 向后兼容：MVP 无历史
- 回滚边界：删库重建

## 9. Definition of Done

- [ ] Spec 中全部 AC 有验证路径
- [ ] 物理数据与 API 契约已引用
- [ ] 内部 Task 候选覆盖完整纵向闭环
- [ ] 自动化测试路径和 CI 门禁明确
- [ ] 手工 / Agent / 外部服务验收没有伪装成自动通过
- [ ] 没有复制 harness-core 开发规范
