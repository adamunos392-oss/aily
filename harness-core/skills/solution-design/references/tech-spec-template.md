# 技术方案文档模板（tech-spec.md）

> 质量线：阶段 C 生成 api-contracts 与 Planner 拆任务拿到本文档零追问开工。所有值定死，禁止"实现时再定"。

## 模板

```markdown
# 技术方案：<项目名>

specification: <规范集名，如 default>

## 1 选型清单

> 逐项从 specification/<集>/backend/tech-stack.md 与 frontend/tech-stack.md 白名单选，写死到库+版本。

| 层 | 选型 | 版本 | 来源白名单 |
|---|---|---|---|
| 后端框架 | FastAPI（基于 pycore APIServer） | x.y.z | backend/tech-stack.md |
| 前端框架 | Vue 3 + TypeScript + Vite | x.y.z | frontend/tech-stack.md |
| 状态管理 | Pinia | x.y.z | frontend/tech-stack.md |
| 前端路由 | Vue Router | x.y.z | frontend/tech-stack.md |
| 数据库 | SQLite | — | backend/tech-stack.md |
| ... | | | |

## 2 页面/功能矩阵

> 页面清单从已确认原型继承（docs/prototypes/），不自行增删；逐条 Feature / AC 映射到页面。

| 页面 | 路由 | Feature / AC | 内容 | 承载功能 | 调用接口 |
|---|---|---|---|---|---|
| 会话问答页 | /conversations | F-004 / AC-F004-01 | 会话列表、消息输入框、转人工按钮 | 会话问答、转人工 | API-F004-01、API-F004-02 |
| ... | | | | | |

## 3 接口设计

> 「接口定义即代码」的方案层表达：模型定清楚，代码层照抄。响应统一走 pycore 信封（success_response / error_response，错误码表见 api-design.md）。每个接口标注路由文件路径，落位规则见 api-design.md「路由文件位置与命名」（一律 `backend/src/api/routes/`，URL 前缀 `/api/<资源复数>`；资源词从 PRD / Feature Map 的名词实体推导，动词不单独成资源——「转人工」是会话上的动作，归入 conversations，不产生 transfer 资源）。每条接口分配 API-Fxxx-xx 编号，api-contracts.md 继承使用。

### 3.x API-F004-01 <接口名>：POST /api/conversations/{id}/transfer

- 来源 Feature：F-004（覆盖 AC：AC-F004-01）
- 路由文件：`backend/src/api/routes/conversations.py`（资源词 conversations 从 Feature Map 功能「会话问答」的名词实体「会话」推出，非从功能措辞另抓词）
- 请求模型：`ConversationTransferRequest`
  - reason: str（必填）
  - target_role: Literal["agent", "admin"]（必填）
- 响应模型：`ConversationSummary`（经 pycore 信封 success_response 包装）
  - conversation_id: int, status: Literal["active", "transferred"], transferred_at: datetime
- 错误码：VALIDATION_ERROR 参数验证失败；NOT_FOUND 会话不存在（错误码表见 api-design.md）
- （逐接口重复此块）

## 4 config 键清单

> 值与选型的单一权威源。方案中出现的所有技术参数与业务数字全部落成键名，代码零硬编码。

| 键名 | 默认值 | 说明 | 使用处 |
|---|---|---|---|
| LLM_MODEL | qwen3-max | 对话模型名 | 问答接口 |
| SEARCH_TOP_K | 5 | 检索返回条数 | 问答接口 |
| DOC_MAX_SIZE_MB | 20 | 单文档上限 | 上传校验 |
| DATABASE_PATH | data/<project-id>.db | SQLite 数据库文件（落点见 env-policy.md「存储落点」，不自造文件名） | 数据库初始化 |
| UPLOAD_DIR | data/uploads | 上传与持久化目录（同上） | 上传接口 |
| ... | | | |

.env 键位策略与端口约定见 specification/<集>/shared/env-policy.md。

## 5 外部服务规格（写死）

> api-design.md「外部服务规格写死」条款的方案层载体：URL、模型名、请求/响应字段方案在这里定死，任何变更 = 技术方案偏航。

| 服务 | URL | 模型/字段 | 用途 | 额度来源 |
|---|---|---|---|---|
| 百炼 | https://dashscope.aliyuncs.com/... | qwen3-max；messages 字段：role/content | 会话问答 | PRD 已有 key |

无外部服务时写"无"。

## 6 风险清单

| 风险 | 影响 | 应对 |
|---|---|---|
| PDF 解析质量不稳定 | 引用不准 | 方案层限定解析库版本并列入选型清单 |
| ... | | |
```

## 填写规则

1. 第 0 行的 `specification:` 必填——下游所有硬引用路径据此参数化；阶段 C5 生成全局 Plan.md 时此行继承进 Plan.md 头部 metadata 行。
2. 选型清单每一行都要能指回白名单文件；指不回的不许出现。
3. 接口设计以 Pydantic 模型为颗粒度，字段类型写完整（含 Literal/可选/默认值），不留"等代码定"；每条接口带 API 编号与来源 Feature。
4. config 键清单与全文数值做交叉检查：任何在 2/3/5 节出现的数字，第 4 节必须有键。
5. 外部服务的 URL、模型名、关键字段写死在方案，不进代码。
