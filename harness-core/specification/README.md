# specification — 规范集库

规范以「规范集」为单位组织，供项目在方案阶段整体选用。agents / skills 只引用路径，规范内容永不复制进 agent 定义。

> 来源说明：default 集由原 `harness-core/dev-standards/` 4 件（frontend / backend-dev / backend-layers / backend-plugin）逐节拆分迁移，并按 V7_2 现值（Vue3 前端、pycore 后端、repositories/ 分层）并入 V8 specification 精华条款。

## 一级结构

```text
specification/
├── default/          # 默认规范集：原 dev-standards 迁移，前端语言/后端框架已约定
│   ├── frontend/     # tech-stack / api-client / mock / style / acceptance
│   ├── backend/      # tech-stack / workflow / layers / api-design / error-handling / plugin
│   └── shared/       # env-policy / naming / security
└── <自建规范集>/      # 学生可自建，如 my-standards/，结构参照 default（件数可少）
```

default 三组语义：`frontend/`、`backend/` 是栈绑定件（换集即整组替换）；`shared/` 是栈无关纪律（自建集默认继承的基底）。

## 规范集选择机制（四条）

1. **问**：B2 末尾确认进入 TS 时向用户问一句「本项目用默认规范集（default）还是自建规范集？」。用户不回答或没有自建集 = default，不阻塞确认。
2. **记**：确认结果记到 `docs/Plan.md` 头部 metadata 行（`specification: <集名>`）——Plan.md 是唯一人类可读全局文件，此行为权威；`ui-design-spec.md` 头部同步记一行；`tech-spec.md` 头部同步记一行（阶段 TS 产物，Plan.md 生成前的中继声明，C5 生成 Plan.md 时继承）。
3. **传**：Planner 生成 tasks.json 时从 Plan.md 头部读出集名，写入 tasks.json 顶层 `"specification"` 字段；任务的 `rules_files` 路径按 `specification/<集名>/...` 占位形式书写（不写死集名），由执行端解析替换。
4. **干活时读哪套**：Planner / Developer / Tester / 开发循环协议四处解析句完全同款——`specification/<集名>/...` 解析为 `harness-core/specification/<集名>/...`：集名优先取 `.sdd/tasks.json` 顶层 `specification` 字段，字段缺失时读取当前项目 `docs/tech-spec.md` 头部 `specification:` 声明，均未声明回落 `default`；解析后的规范文件不存在必须停下报出，禁止静默降级。自建集放 `harness-core/specification/<集名>/`（全局放，跨项目复用）。

## 条款元标准（写规范的规范）

1. **可判定**：每条规范必须能被一个具体动作判对错（验收写法），写不出验收动作的条款不进规范集。
2. **单一权威源**：同一件事只在一个文件里写死，其他文件只指向它，禁止多处重复展开（改一处漏一处）。
3. **正反例优先**：易错条款必须配正例+反例，用具体 JSON/命令/代码片段表达，不写抽象形容词。

## 经验九条（规范体系的实证经验）

1. 条款三件套=要求+判定+消费方（五态条款实证）。
2. 模板示例=最强传染源（规范与示例不一致时示例赢；改规范必改齐示例）。
3. skill 不复制条款只硬引用+圈消费范围。
4. 并发互不可见→共同上级约束或事后单一基准（「让 A 参考 B」并发下必失效）。
5. 对齐点不输出基准=没对齐（打回必带「字段=值+来源」照抄）。
6. 自报≠done（产物实查+逐条断言+证据原文）。
7. 封闭枚举>单例提示。
8. 对偶约束写两侧（禁自造+标待确认，不写「遵循对方」）。
9. 责任链：PRD 定业务、方案定值、规范定纪律、代码零决策；原型只回答「长什么样」。

## default 规范集索引（正反向：内容 + 谁消费）

| 文件 | 内容 | 消费方 |
|------|------|--------|
| frontend/tech-stack.md | Vue3+TS+Pinia+Vue Router 白名单 + 总则 + 目录结构 | Planner（rules_files 分配）/ Developer / Tester |
| frontend/api-client.md | axios 封装 / 路由守卫 / Vite 代理配置 / 常见错误对照 | Developer / Tester |
| frontend/mock.md | Mock 集中管理 / 格式对齐 api-contracts / Endpoint DTO 收敛 | Developer（前端任务）/ Tester（Mock 阶段验证） |
| frontend/style.md | 原型参考（强制）+ 设计底线 + 交互五态 + 布局易错点 | Developer（写码）/ Tester（样式对齐校验）；原型环节不消费五态条 |
| frontend/acceptance.md | Plan.md 维护 + 开发节奏 + 自动验收清单 | Developer / Tester |
| backend/tech-stack.md | Python/FastAPI/pycore 白名单 + 值单一权威源 + Python 环境 + 环境与工具链硬性禁止 + PyCore 核心配置 | Planner / Developer / Tester |
| backend/workflow.md | 权限边界 + 阶段判断 + 首次进入 + 逐功能开发 + 测试纪律 + 交付 | Planner / Developer / Tester |
| backend/layers.md | 模型层 / 数据访问层 / Service 层规范 + 易错点 | Developer / Tester（分层检查） |
| backend/api-design.md | 接口定义即代码 + 统一信封 + 错误码 + 路由落位与资源词推导 + 认证依赖 | 产品设计阶段（tech-spec 接口清单 + api-contracts 产出）/ Developer / Tester |
| backend/error-handling.md | 错误处理链路 + 异常使用速查 + 四类错误分类审核 | Developer / Tester |
| backend/plugin.md | PyCore Plugin 层（仅 AI Agent 应用） | Developer（Agent 任务）/ Tester |
| shared/env-policy.md | .env 策略 + 端口唯一权威表 + 存储落点唯一权威表 | 前后端全部任务 + 产品设计阶段 |
| shared/naming.md | 前后端命名规范归一 | Developer / Tester |
| shared/security.md | 密钥红线 + 外部服务调用红线（最高优先级，违反即停） | 全部（Planner / Developer / Tester / 产品设计阶段） |
