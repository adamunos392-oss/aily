# 阶段 C：技术契约、Feature Plan 与全局开发计划

阶段 C 必须从已经确认的 Feature Map、Domain Model、Feature Spec 和原型反推技术契约。禁止先按数据库 CRUD 或现有代码结构设计接口，再回头迁就功能。

## 前置条件

- `docs/PRD.md` 的产品定义已确认
- `docs/feature-map.md` 已确认
- `docs/domain-model.md` 已确认
- 全部 MVP `docs/features/*/spec.md` 状态为 `Ready`
- 原型已完成并通过 Feature / AC 追踪检查
- `docs/tech-spec.md` 已确认（选型 / 接口形态 / config 键已定，产出见 `harness-core/agents/solution-designer.md`）

任一条件不满足，返回对应阶段修正。

## 固定产出

```text
docs/
├── PRD.md
├── feature-map.md
├── domain-model.md
├── ui-design-spec.md
├── tech-spec.md
├── data-model.md
├── api-contracts.md
├── Plan.md
├── prototypes/
└── features/
    └── F-xxx-<slug>/
        ├── spec.md
        └── plan.md
```

## 执行顺序

```text
C1 PRD 最终定稿
→ C2 从 Feature 数据责任反推 data-model.md
→ C3 从 Feature 流程与 AC 反推 api-contracts.md
→ C4 为每个 MVP Feature 生成 plan.md
→ C5 生成全局 Plan.md
→ C6 Traceability / Feature Ready 自检
```

---

## C1：PRD 最终定稿

在阶段 A 的产品定义基础上补充：

- 已确认的 Feature Map 摘要和路径
- 原型说明及 Feature / AC 对应关系
- 版本路线图终版
- 产品级技术架构蓝图（只描述系统边界和技术选择，不复制接口或字段；选型值以 `docs/tech-spec.md` 选型清单为权威，PRD 不重复展开）
- 外部服务选择、风险和降级原则
- 变更记录

PRD 继续作为产品层事实来源，不承载：

- 物理数据库字段明细
- API 请求/响应 DTO 明细
- Feature 内部实施任务
- 开发运行状态

这些内容分别进入 `data-model.md`、`api-contracts.md`、Feature `plan.md` 和 `.sdd/tasks.json`。

---

## C2：输出物理数据模型（data-model.md）

必须输出 `docs/data-model.md`。

数据模型必须从以下资料反推：

1. `domain-model.md` 中的业务对象、关系和状态机
2. `feature-map.md` 中的读写关系和数据 Owner
3. 每个 Feature Spec 的业务数据读写、业务规则和 AC
4. 原型中已确认的展示、筛选和输入需求

### 固定结构

```markdown
# 数据模型

> 物理数据结构的唯一事实来源。每个实体和字段必须能追溯到 Feature 或通用基础设施需求。

## 1. 数据设计原则

- 数据库类型：
- ID 策略：
- 时间与时区：
- 软删除 / 归档策略：
- 审计策略：

## 2. 实体总览

| 实体/表 | 业务对象 | Owner Feature | 读写 Feature | 生命周期 |
|---|---|---|---|---|
| tickets | 工单 | F-004 | F-004/F-005/F-006 | 待处理 → 处理中 → 已完成 |

## 3. 实体定义

### tickets

| 字段 | 类型 | 必填 | 默认值 | 业务含义 | 来源 Feature/AC | 约束 |
|---|---|---|---|---|---|---|
| conversation_id | integer | 是 | - | 关联原始会话 | F-004 / AC-F004-01 | 同一会话最多一张活动工单 |

## 4. 关系与约束

- 外键关系
- 唯一约束
- 状态约束
- 并发不变量

## 5. 索引与查询依据

| 索引 | 服务查询 | 来源 Feature/AC | 原因 |
|---|---|---|---|

## 6. 数据迁移与兼容性

- 初始建表
- 变更策略
- 回滚边界
```

### 数据字段规则

- 每个业务字段必须标明来源 Feature 或 AC
- 只有通用基础设施字段（如 `id`、`created_at`）可以标为 `platform`
- 没有来源的字段不得加入 MVP 数据模型
- Feature Spec 的业务语义优先于方便 CRUD 的字段设计
- Domain Model 变化时，必须重新检查受影响 Feature Spec、API 和测试

---

## C3：输出 API 契约（api-contracts.md）

必须输出 `docs/api-contracts.md`。

接口按 Feature 的业务动作组织，不按数据库表机械生成 CRUD。

**tech-spec 消费规则**：接口的技术形态（路由、请求/响应模型、错误码、资源词、路由文件落位）以 `docs/tech-spec.md` §3 接口设计为权威输入，在其基础上补齐 Feature / AC 追踪、鉴权、幂等与数据影响，不推翻重设计；发现 tech-spec 缺陷时报告用户返回阶段 TS 修正，不得在 api-contracts 里绕开另设一套。接口的 `API-Fxxx-xx` 编号沿用 tech-spec 已分配的编号。

### 通用契约先确认

在具体 endpoint 之前确认：

- 统一成功 / 错误响应格式
- HTTP 状态码原则
- 分页、排序和筛选约定
- 鉴权方式
- 幂等性原则
- 时间、枚举和空值表示
- 错误码命名规则

### 每个 endpoint 必须包含

```markdown
## API-F004-01 转人工

- 来源 Feature：F-004
- 覆盖 AC：AC-F004-01、AC-F004-02
- 业务动作：员工把当前咨询转为人工处理
- Method / Path：POST /api/conversations/{id}/transfer
- 权限：已登录员工
- 幂等性：同一会话重复调用不得创建第二张活动工单

### 请求

- Path 参数：
- Query 参数：
- Request Body：完整字段、类型、必填与约束

### 成功响应

- HTTP 状态：
- 完整 JSON Schema / 示例：禁止 `...` 占位

### 失败响应

| 场景 | HTTP 状态 | 业务错误码 | 返回内容 |
|---|---|---|---|

### 数据影响

- 读取实体：
- 创建实体：
- 修改实体：
- 状态变化：
```

### 契约规则

- 每个 endpoint 必须引用 Feature ID 和 AC ID
- 每个 MVP AC 涉及的后端行为必须能找到 endpoint、事件或明确的“无 API”说明
- 请求 / 响应字段必须来自 `data-model.md` 或明确的派生 DTO
- 禁止直接暴露内部实体；DTO 字段需要独立说明
- Mock、前端类型、后端模型和测试都以本文档为契约来源
- 禁止使用 `...`、`TBD` 或无法判定的占位符

---

## C4：为每个 MVP Feature 生成 plan.md

路径：

```text
docs/features/F-001-user-login/plan.md
```

Feature Plan 定义“如何实现已经确认的 Feature Spec”，不得修改用户结果、业务规则和 AC。发现 Spec 不完整时必须返回阶段 F；Plan 不得补写新需求。

### 固定模板

```markdown
# F-001 用户登录实施计划

## 1. 追踪信息

- Feature：F-001
- Spec：docs/features/F-001-user-login/spec.md
- Spec 版本：1
- 依赖 Feature：无
- Data Model：docs/data-model.md 相关章节
- API：API-F001-01、API-F001-02
- 原型：docs/prototypes/... 对应 Frame

## 2. 实现策略

- 前端实现路径：
- 后端实现路径：
- 状态管理：
- 数据持久化：
- 外部服务：
- 权限与安全：

## 3. 影响范围

| 层级 | 预计模块/目录 | 变更目的 | 禁止影响 |
|---|---|---|---|

## 4. 内部 Task 候选

| Task 候选 | 类型 | 产出 | 依赖 | 覆盖 AC |
|---|---|---|---|---|
| 后端认证实现 | backend | API、领域服务、单测 | 基础设施 | AC-F001-01/02 |
| 前端真实联调 | frontend/integration | service、store、页面 | 后端认证 | AC-F001-01/02 |
| Feature 测试 | test | API / E2E 测试 | 前后端完成 | 全部 |

> 此表供 Planner 生成 `.sdd/tasks.json`。任务运行状态统一记录在 `.sdd/tasks.json`。

## 5. 开发规范引用

- harness-core/dev-standards/frontend.md
- harness-core/dev-standards/backend-dev.md
- harness-core/dev-standards/backend-layers.md
- AI Agent Feature 按需增加 backend-plugin.md

只引用核心规范，不复制内容。

## 6. AC → 测试映射

| AC | 验证类型 | 测试层级 | 计划测试路径 | 确定性命令 | CI 门禁 |
|---|---|---|---|---|---|
| AC-F001-01 | auto | E2E | e2e/features/f001-login.spec.ts | Playwright | required |
| AC-F001-02 | auto | API | backend/tests/features/f001/test_login.py | Pytest | required |

## 7. 外部服务与测试权限

| 服务 | 配置字段 | Tester 权限 | 缺失时策略 | 可否宣称完整通过 |
|---|---|---|---|---|

## 8. 风险、迁移与回滚

- 风险：
- 数据迁移：
- 向后兼容：
- 回滚边界：

## 9. Definition of Done

- [ ] Spec 中全部 AC 有验证路径
- [ ] 物理数据与 API 契约已引用
- [ ] 内部 Task 候选覆盖完整纵向闭环
- [ ] 自动化测试路径和 CI 门禁明确
- [ ] 手工 / Agent / 外部服务验收没有伪装成自动通过
- [ ] 没有复制 harness-core 开发规范
```

### Feature Plan 规则

- Feature Plan 记录实施设计；运行进度统一记录在全局 Plan 和 `.sdd/tasks.json`
- 一个 Feature 可以拆多个内部 Task
- 内部 Task 可以按前端、后端、测试拆分，但 Feature 只有在完整纵向闭环通过后才能验收
- Feature Plan 不直接触发子智能体；Planner 在开发入口把它编译为任务状态机
- Spec 版本变化后，Plan 必须重新检查并更新追踪信息

---

## C5：生成全局 Plan.md

`docs/Plan.md` 是人类可读的项目路线图和进度总览，不展开每个 Feature 的实现细节。

### 固定结构

```markdown
# 全局开发计划

## 1. Feature 交付总览

| Feature | 用户结果 | 依赖 | Spec | Plan | 优先级 | 状态 |
|---|---|---|---|---|---|---|
| F-001 | 用户登录 | 无 | features/F-001/spec.md | features/F-001/plan.md | MVP | Ready |

## 2. 交付依赖图

## 3. 前端 Mock 验收阶段

- 页面 / Feature / AC 映射
- 原型验收门禁
- Mock 数据必须符合 API 契约

## 4. 后端基础设施阶段

- 项目结构
- 配置和数据库
- 健康检查
- 通用认证 / 中间件（仅确属跨 Feature 基础设施时）

## 5. 逐 Feature 纵向闭环阶段

| 顺序 | Feature | 完整闭环 | 用户门禁 |
|---|---|---|---|

## 6. 外部服务与测试权限清单

| 服务 | 用途 | 配置字段 | Tester 权限 | 缺失策略 | 状态 |
|---|---|---|---|---|---|

## 7. 最终回归与交付

- 跨 Feature E2E
- 启动文档
- 部署前检查
```

### Plan 维护规则

- `docs/Plan.md` 是唯一的人类可读全局进度文件
- Feature `plan.md` 只描述实施方案，不记录运行进度
- `.sdd/tasks.json` 是机器执行状态，由开发入口生成
- 全局 Plan 的 Feature 状态必须与任务状态机同步，不得出现两套冲突事实

---

## C6：Traceability / Feature Ready 自检

### 完整追踪链

每个 MVP 需求必须能够形成：

```text
PRD 场景 / 业务规则
→ Feature
→ Acceptance Criteria
→ Domain Object / State
→ Data Field / API Contract
→ Feature Plan
→ Planned Test
→ 后续 Task / CI Result
```

### 自检清单

- [ ] PRD 没有承载物理字段或 API DTO 明细
- [ ] tech-spec 的选型与 config 键被 data-model、api-contracts、Plan 一致引用，未另设一套
- [ ] 每个物理字段都有 Feature/AC 或 platform 来源
- [ ] 每个 endpoint 都有 Feature/AC 来源
- [ ] 每个 MVP Feature 都有 Ready Spec 和完整 Plan
- [ ] 每条 auto AC 都有计划测试层级、路径和命令
- [ ] manual / agent / external AC 没有被标记为确定性自动通过
- [ ] Feature Plan 只引用核心开发规范，没有复制规则
- [ ] 全局 Plan 只维护路线图和总进度
- [ ] 无 `TBD`、`...`、缺失依赖或循环依赖
- [ ] 原型、数据模型和 API 没有引入 Spec 范围外的新需求

自检不通过时，返回对应阶段修复，不得进入 Planner / Developer / Tester 开发循环。

## 阶段 C 完成门禁

向用户展示：

- Feature 交付顺序
- 每个 Feature 的 Spec / Plan 状态
- 数据与 API 契约追踪结果
- AC → 测试映射覆盖率
- 外部服务与降级项
- 尚需人工判断的 AC

发起：

> 产品定义、Feature 架构、原型、数据模型、API 契约和 Feature Plan 已完成。请审核这些产物；确认后才可以使用 `/sdd-start` 让 Planner 生成任务状态机。

未经用户确认，不得进入开发阶段。
