# F-005 查询可用会议室实施计划

## 1. 追踪信息

- Feature：F-005
- Spec：docs/features/F-005-meeting-room-query/spec.md
- Spec 版本：1
- 依赖 Feature：F-001
- Data Model：docs/data-model.md 中 conversations、turns、meeting_rooms、trace_events、confirmations、meetings
- API：API-F002-01、API-F002-02
- 原型：docs/prototypes/01-workbench.html（查询信息入口、会议室列表）

## 2. 实现策略

- 前端实现路径：快捷「查询信息」预置问句；展示 room_list；事件流无确认节点
- 后端实现路径：intent `query_meeting_rooms` → READ_TOOL → meeting_room_query；空列表不编造成功预订
- 状态管理：本轮 TurnResponse
- 数据持久化：meeting_rooms seed；不写 confirmations/meetings
- 外部服务：Mock Tool
- 权限与安全：只读

## 3. 影响范围

| 层级 | 预计模块/目录 | 变更目的 | 禁止影响 |
|---|---|---|---|
| 前端 | `RoomListMessage.vue` | 展示可用会议室 | 不得出确认卡 |
| 后端 | `ReadToolPlugin`、`tool_adapter.py` | 会议室查询 | 不得创建会议 |
| 数据 | meeting_rooms | seed | 无 |

## 4. 内部 Task 候选

| Task 候选 | 类型 | 产出 | 依赖 | 覆盖 AC |
|---|---|---|---|---|
| 会议室 READ_TOOL | backend | turns 查询链、单测 | F-001 | AC-F005-01～03 |
| 查询结果 UI | frontend/integration | 列表与空态 | 会议室 READ_TOOL | AC-F005-01～03 |
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
| AC-F005-01 | auto | API | backend/tests/features/f005/test_room_query.py | python3.11 -m pytest backend/tests/features/f005/test_room_query.py --timeout=120 | required |
| AC-F005-02 | auto | API | backend/tests/features/f005/test_read_only_no_meeting.py | python3.11 -m pytest backend/tests/features/f005/test_read_only_no_meeting.py --timeout=120 | required |
| AC-F005-03 | auto | API | backend/tests/features/f005/test_empty_rooms.py | python3.11 -m pytest backend/tests/features/f005/test_empty_rooms.py --timeout=120 | required |
| AC-F005-01～03 | auto | E2E | e2e/features/f005-rooms.spec.ts | npx playwright test e2e/features/f005-rooms.spec.ts | required |

## 7. 外部服务与测试权限

| 服务 | 配置字段 | Tester 权限 | 缺失时策略 | 可否宣称完整通过 |
|---|---|---|---|---|
| Mock Tool | `MEETING_ROOM_QUERY_AFTER_HOUR`、`MEETING_ROOM_QUERY_DEMO_DATE_OFFSET_DAYS` | 本地默认 | 测试失败 | 否 |

## 8. 风险、迁移与回滚

- 风险：查询路径误走 create_meeting
- 数据迁移：seed 会议室
- 向后兼容：MVP 无历史
- 回滚边界：删库重建

## 9. Definition of Done

- [ ] Spec 中全部 AC 有验证路径
- [ ] 物理数据与 API 契约已引用
- [ ] 内部 Task 候选覆盖完整纵向闭环
- [ ] 自动化测试路径和 CI 门禁明确
- [ ] 手工 / Agent / 外部服务验收没有伪装成自动通过
- [ ] 没有复制 harness-core 开发规范
