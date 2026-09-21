# 全局开发计划

specification: default

## 1. Feature 交付总览

| Feature | 用户结果 | 依赖 | Spec | Plan | 优先级 | 状态 |
|---|---|---|---|---|---|---|
| F-001 | 独立对话上下文与身份 | 无 | features/F-001-conversation-context/spec.md | features/F-001-conversation-context/plan.md | MVP | Ready |
| F-002 | 企业知识有据问答与拒答 | F-001 | features/F-002-enterprise-knowledge-qa/spec.md | features/F-002-enterprise-knowledge-qa/plan.md | MVP | Ready |
| F-003 | Skill 创建会议（含确认/超时/作废） | F-001 | features/F-003-create-meeting/spec.md | features/F-003-create-meeting/plan.md | MVP | Ready |
| F-004 | 生成本周周报并可编辑 | F-001 | features/F-004-weekly-report/spec.md | features/F-004-weekly-report/plan.md | MVP | Ready |
| F-005 | 查询可用会议室 | F-001 | features/F-005-meeting-room-query/spec.md | features/F-005-meeting-room-query/plan.md | MVP | Ready |
| F-006 | Demo 验证台对照（非员工产品功能） | 无 | features/F-006-evaluation-cases/spec.md | features/F-006-evaluation-cases/plan.md | Demo Validation | Ready |

员工侧 MVP 产品 Feature：F-001～F-005。F-006 不计入员工产品 Feature，但必须随 Demo 交付。

## 2. 交付依赖图

```text
基础设施（SQLite / pycore / Mock UserContext / PluginRegistry）
        │
        ▼
     F-001 对话与身份
        │
        ├──────────► F-002 知识问答
        ├──────────► F-005 会议室查询
        ├──────────► F-003 创建会议
        └──────────► F-004 周报
                         │
                         ▼
              F-006 Demo 验证台（预置快照，不依赖员工操作写回）
```

无循环依赖。F-002～F-005 共享 `API-F002-01` 编排入口，实现上可先落地编排骨架再按 Feature 填 Plugin。

## 3. 前端 Mock 验收阶段

- 页面：`/` 工作台覆盖 F-001～F-005；`/demo/evaluation` 仅 F-006
- Mock 数据必须符合 `docs/api-contracts.md` 信封与 DTO
- 原型门禁：与 `docs/prototypes/01-workbench.html`、`docs/prototypes/demo/evaluation.html` 及 `docs/ui-design-spec.md` 一致
- 前端 Mock 只经 service 层，禁止写在 Vue 组件

## 4. 后端基础设施阶段

- 项目结构：tech-spec §7（routes / plugins / services / repositories/mock / models/agent）
- 配置：tech-spec §4 全部键；`DATABASE_PATH=data/aily.db`；端口 8099 / 5199
- 数据库：create_all + seed（知识、人员、会议室、工作消息、7 评测案例、超时演示对话）
- 健康检查：pycore 默认
- 认证：无登录；`deps.get_current_user` → Mock UserContext
- Python：3.11+（开发机若仅 3.9 须先具备 3.11+）

## 5. 逐 Feature 纵向闭环阶段

| 顺序 | Feature | 完整闭环 | 用户门禁 |
|---|---|---|---|
| 1 | F-001 | 新建/切换/列表/身份 | 侧栏与顶栏可用 |
| 2 | F-002 | 差旅有据问答 + 拒答 + 事件流 | S-001/S-002 |
| 3 | F-005 | 会议室只读查询 | S-005 |
| 4 | F-003 | 澄清/消歧/确认/成功/超时/作废/执行任务 | S-003/S-006/S-007 |
| 5 | F-004 | 周报生成与编辑 | S-004 |
| 6 | F-006 | Demo 列表/回放/工作台无评测入口 | S-008 |

## 6. 外部服务与测试权限清单

| 服务 | 用途 | 配置字段 | Tester 权限 | 缺失策略 | 状态 |
|---|---|---|---|---|---|
| Mock Rewrite/Intent/Slot/Router/RAG/Tool/Skill | Agent 节点 | `MOCK_MODE` 等，见 tech-spec §4/§5 | 本地默认 true | 对应场景失败，禁止编造 | 计划内 |
| Mock Evaluation | Demo 对照 | `EVALUATION_CASE_COUNT_EXPECTED` | 本地默认 | 验证台失败 | 计划内 |
| 真实 LLM / 飞书 / Aily | 非 MVP | 无 | 无 | 不接入 | 禁止 |

## 7. 最终回归与交付

- 跨 Feature E2E：工作台走完 S-001～S-007；单独打开 `/demo/evaluation` 核验 AC-F006-05
- 启动文档：Agent 端口 5199/8099；用户验收端口 5175/8003
- 部署前检查：`MOCK_MODE=true`；员工导航无评测；超时文案无「会议已创建」
