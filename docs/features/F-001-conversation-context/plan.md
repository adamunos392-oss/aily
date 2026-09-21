# F-001 维护独立对话上下文实施计划

## 1. 追踪信息

- Feature：F-001
- Spec：docs/features/F-001-conversation-context/spec.md
- Spec 版本：1
- 依赖 Feature：无
- Data Model：docs/data-model.md 中 conversations、turns、confirmations
- API：API-F001-01、API-F001-02、API-F001-03、API-F001-04
- 原型：docs/prototypes/01-workbench.html（左栏会话、顶栏身份）

## 2. 实现策略

- 前端实现路径：工作台布局、会话列表、新建/切换、身份展示；只调 `/api/identity` 与 `/api/conversations*`
- 后端实现路径：`identity.py` + `conversations.py`；`get_current_user` 注入 Mock UserContext；ConversationService + ConversationRepository
- 状态管理：Pinia conversation store，按 `conversation_id` 隔离
- 数据持久化：SQLite `conversations` / `turns`
- 外部服务：无
- 权限与安全：所有查询过滤 `user_id=MOCK_USER_ID`；无登录

## 3. 影响范围

| 层级 | 预计模块/目录 | 变更目的 | 禁止影响 |
|---|---|---|---|
| 前端 | `frontend/src/views/WorkbenchView.vue`、`stores/conversation.ts`、`services/identity.ts` | 工作台壳与会话 | 不得渲染评测导航或 evaluation_cases |
| 后端 | `api/routes/identity.py`、`conversations.py`、`deps.py` | 身份与对话 CRUD 读 | 不得实现登录/JWT |
| 数据 | `models` conversations | 建表 seed 含超时演示对话行 | 不得删除预置 `MEETING_TIMEOUT_DEMO_CONVERSATION_ID` |

## 4. 内部 Task 候选

| Task 候选 | 类型 | 产出 | 依赖 | 覆盖 AC |
|---|---|---|---|---|
| 对话与身份 API | backend | identity/conversations 路由、仓储、单测 | 基础设施 | AC-F001-01～04 |
| 工作台会话 UI | frontend/integration | 页面、store、service | 对话与身份 API | AC-F001-01～04 |
| Feature 测试 | test | API + E2E | 前后端完成 | 全部 |

> 此表供 Planner 生成 `.sdd/tasks.json`。任务运行状态统一记录在 `.sdd/tasks.json`。

## 5. 开发规范引用

- 规范集：harness-core/specification/default/（集名=Plan.md 头部 specification: 声明，缺省 default）
- 前端任务：specification/default/frontend/（tech-stack / api-client / mock / style）+ shared/（env-policy / naming / security）
- 后端任务：specification/default/backend/（tech-stack / layers / api-design / error-handling）+ shared/（env-policy / naming / security）

只引用路径，不复制内容。

## 6. AC → 测试映射

| AC | 验证类型 | 测试层级 | 计划测试路径 | 确定性命令 | CI 门禁 |
|---|---|---|---|---|---|
| AC-F001-01 | auto | API | backend/tests/features/f001/test_create_conversation.py | python3.11 -m pytest backend/tests/features/f001/test_create_conversation.py --timeout=120 | required |
| AC-F001-02 | auto | API | backend/tests/features/f001/test_switch_conversation.py | python3.11 -m pytest backend/tests/features/f001/test_switch_conversation.py --timeout=120 | required |
| AC-F001-03 | auto | API | backend/tests/features/f001/test_list_conversations.py | python3.11 -m pytest backend/tests/features/f001/test_list_conversations.py --timeout=120 | required |
| AC-F001-04 | auto | API | backend/tests/features/f001/test_identity.py | python3.11 -m pytest backend/tests/features/f001/test_identity.py --timeout=120 | required |
| AC-F001-01～04 | auto | E2E | e2e/features/f001-conversation.spec.ts | npx playwright test e2e/features/f001-conversation.spec.ts | required |

## 7. 外部服务与测试权限

| 服务 | 配置字段 | Tester 权限 | 缺失时策略 | 可否宣称完整通过 |
|---|---|---|---|---|
| 无 | 无 | 无 | 无 | 是（纯本地 Mock 身份） |

## 8. 风险、迁移与回滚

- 风险：切换对话串用 slot/confirmation
- 数据迁移：初始建表
- 向后兼容：MVP 无历史
- 回滚边界：删除 SQLite 文件

## 9. Definition of Done

- [ ] Spec 中全部 AC 有验证路径
- [ ] 物理数据与 API 契约已引用
- [ ] 内部 Task 候选覆盖完整纵向闭环
- [ ] 自动化测试路径和 CI 门禁明确
- [ ] 手工 / Agent / 外部服务验收没有伪装成自动通过
- [ ] 没有复制 harness-core 开发规范
