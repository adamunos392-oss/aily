# 后端开发工作流（default）

> 来源：原 dev-standards/backend-dev.md 头部权限块 + 阶段判断 + 首次进入（§2/§3）+ 逐功能开发 + 交付 + 测试库隔离条。环境、选型与 pycore 用法见 tech-stack.md；分层规范见 layers.md；接口规范见 api-design.md。

## 权限边界

- **依赖安装**：项目虚拟环境内的 `pip install` / `uv sync` / `pip install -r requirements.txt` 可由 Agent 自动执行；全局安装、`sudo`、系统 Python 修改、涉及密钥或付费资源的命令必须先向用户确认。
- **测试**：后端单元测试、lint、typecheck、短时启动检查、curl 验证可由 Agent 自动执行；需要人工业务验收的部分才交给用户操作。

---

## 阶段判断

通过检查全局 Plan 与任务状态判断当前处于后端开发的哪个阶段：

- `docs/Plan.md` 中没有「后端基础设施阶段」或尚未记录 Python 环境 → **初始化阶段**（执行下方「首次进入后端开发」）
- 「后端基础设施阶段」存在未完成项 → **基础设施阶段**
- 后端基础设施已完成，且存在待执行 Feature Task → **功能开发阶段**（执行下方「逐功能开发」）

---

## 首次进入后端开发（仅执行一次）

以下步骤在后端开发启动时执行，完成后不再重复。

### 1. 自动探测 Python 指令

Agent 自动探测 Python 3.11+ 指令、创建 `.venv` 并安装依赖——完整流程见 `backend/tech-stack.md`「Python 环境与虚拟环境」。

### 2. 复核 .env 配置与外部服务权限

进入后端开发前，Orchestrator 已经执行「外部服务与 Tester 权限门禁」。本阶段必须复核该清单，并把确认后的字段落到 `.env.example` / `.env` 中。

列出后端需要的所有配置项，让用户逐项确认值。示例：

```env
# 数据库
DATABASE_URL=sqlite+aiosqlite:///./app.db

# 服务
HOST=0.0.0.0
PORT=8099
DEBUG=true

# CORS
CORS_ORIGINS=["http://localhost:5199","http://127.0.0.1:5199","http://localhost:5175","http://127.0.0.1:5175"]

# AI/LLM（如需要）
LLM_API_KEY=
LLM_MODEL_NAME=
LLM_BASE_URL=
```

**根据项目实际需求列出配置项，上面只是示例。需要真实密钥、付费资源、外部账号、回调地址、测试账号或 Tester 完整联调权限时，必须在进入自动化开发前一次性向用户确认。普通占位配置、SQLite、本地 Mock 服务不得阻塞后端编码。**

**Tester 权限要求：**
- 必要服务 Key / 测试账号 / Base URL / 回调配置缺失时，不得宣称完整联调通过
- 用户明确选择不提供时，必须在 Plan.md / tasks.json 中标记为 Mock/fallback 降级开发
- 真实 Key 不得写入 PRD、Plan、tasks.json、测试报告、完成报告、BUG 日志、经验文件、README 或任何 `.md` / `.json` 可读产物；只能写入 `.env` 等配置文件，示例文件只写字段名和占位值（红线全文见 `shared/security.md`）

### 3. 补充 Plan.md 后端部分

**`docs/Plan.md` 在设计阶段 C 已由 Agent 生成初始版本**（包含 Feature 交付总览、依赖图、开发阶段和外部服务清单）。物理数据契约位于 `docs/data-model.md`，Feature 实施细节位于 `docs/features/*/plan.md`。首次进入后端开发时，需要补充后端专属信息：

**补充内容：**
- Python 环境信息（Agent 探测到的 Python 指令、项目内 `.venv`）
- 后端功能清单的依赖关系确认
- .env 配置确认结果
- 外部服务与 Tester 权限确认结果

**拆解原则：**
- 按 **能力依赖** 拆，绝不按页面或菜单顺序排开发优先级
- 由 Planner / Developer / Tester 在多智能体开发阶段内部确认；只有涉及架构级取舍或 PRD/API 契约歧义时才询问用户
- **数据与调用链优先**：先有 DB + 可写可读，再做检索/生成等上层能力
- 先列出所有功能，再标注依赖关系，最后按依赖拓扑排序

**示例：电商系统**
```
错误（按页面）：首页功能 → 商品页 → 购物车 → 订单
正确（按依赖）：用户认证 → 商品管理 → 购物车 → 订单 → 支付
```

**在 Plan.md「后端基础设施阶段」中补充 Python 环境信息：**

```markdown
### Python 环境
- **Python 指令**：`<Agent 探测到的 3.11+ 指令>`
- **虚拟环境**：`.venv`
- [ ] Agent 已确认 Python 指令（`<指令> --version` 输出 3.11.x 或更高）
```

> Plan.md 的完整模板和维护规则定义在 `harness-core/skills/sdd-product-design/phase-C.md` 阶段 C5 中。

完成以上第 1～3 步后，直接进入后端编码阶段。除非 PRD / API 契约存在歧义或涉及架构级决策，不得向用户发起推进确认。

---

## 逐功能开发（日常执行）

### 进入每个 Feature 前：读取已确认 Spec / Plan（必须）

**开发任意功能（含基础设施）之前，必须先执行以下流程：**

```
1. 从任务 source_feature 获取 Feature ID
2. 读取 docs/features/<feature-id>/spec.md，确认用户结果、边界和 AC
3. 读取 docs/features/<feature-id>/plan.md，确认分层方案、内部 Task 候选、测试映射和 rules 引用
4. 读取 docs/domain-model.md、docs/data-model.md 和 docs/api-contracts.md 的相关章节
5. 确认 Task 没有超出 Feature Plan；若 Spec/Plan 缺失、版本不一致或 AC 无验证路径，停止并返回产品设计阶段
```

**禁止**：开发阶段临时生成另一份 Feature Plan、把实现思路追加到全局 `Plan.md`、修改 AC 或自行扩大 Feature 范围。

---

### 分层开发顺序

每个功能内部按从下往上的顺序开发：

```
models/（Pydantic）→ db/models.py（ORM）→ repositories/
  → services/ → api/deps.py → api/routes/
```

**原则**：每一层只依赖它下面的层，不得反向依赖。各层规范见 `layers.md`（模型/数据访问/Service）与 `api-design.md`（路由层）。

### 开发节奏

```
功能 N：
  读取 Feature Spec/Plan → 按 Planner 编译的内部 Tasks 执行
  → 按计划逐层实现
  → 后端功能完成后，立即修正对应前端 service / store / page → VITE_USE_MOCK=false 时调用真实后端
  → Tester/Agent 自动执行前端真实联调检查 + 终端接口测试
  → 自动验证通过 → Plan.md 状态改为「已完成」
  → 功能 N+1（按依赖顺序）
```

---

### 每个功能完成后：Agent 先测试，再提供验收指令（强制）

**后端功能完成 + 对应前端切换到真实接口后，Agent 必须先自行执行可自动化的验证命令。**

**提交前必查清单（强制）：**

```
□ python3.11 -m ruff check backend/src backend/tests 通过
□ python3.11 -m mypy backend/src backend/tests 通过
□ python3.11 -m pytest backend/tests --timeout=120 通过（如有新增/修改测试；pytest-timeout 插件缺失先装再测，禁止裸跑，门禁见 backend/tech-stack.md「硬性禁止」）
□ backend/tests 使用独立测试库或事务回滚；未对运行时业务库执行 drop_all / 清表；pytest 后真实库核心表与 seed 数据仍存在
□ 涉及数据库字段 → 对照 docs/data-model.md 核对字段名、类型、约束及 Feature/AC 来源
□ 涉及外部服务 → 至少执行1次真实调用，打印响应结构确认解析正确；HTTP 客户端显式 `trust_env=False`，未继承本机代理/证书/系统环境
□ 代码无硬编码密钥
```

执行顺序：

1. Agent 自行启动/调用必要的短时验证命令（lint、typecheck、unit test、curl、构建检查等）。
2. Agent 记录验证结果；**失败时先自行修复，不能直接把错误甩给用户**。
3. 对 Web 项目后端业务任务，Agent/Tester 必须验证 `VITE_USE_MOCK=false` 的真实前后端路径；只验证 curl 不足以通过。
4. 只有需要人工界面验收的部分，才交给用户操作。
5. 最终仍要向用户提供两套验收方式，方便复现。

```
【功能测试指令】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 已完成：[功能名称]
📍 修改文件：[列出修改的文件]

🖥️ 前端测试（用户操作页面验证）：
  1. 启动后端：cd backend && PYTHONPATH=.. <python指令> -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8003
  2. 启动前端：cd frontend && VITE_BACKEND_PROXY_TARGET=http://localhost:8003 npm run dev -- --host 127.0.0.1 --port 5175
  3. 打开浏览器访问：http://localhost:5175
  4. 操作步骤：
     - [具体操作，如：进入登录页，输入 test@test.com / 123456]
     - [具体操作，如：点击登录按钮]
  5. 预期结果：
     - [如：页面跳转到首页，右上角显示用户名]

💻 终端测试（curl 命令验证接口）：
  # 测试 [接口名称]
  curl -X POST http://localhost:8003/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "test@test.com", "password": "123456"}'

  # 预期返回：
  # {"code": 200, "data": {"access_token": "...", "user": {...}}}

⚠️ 我已先完成自动化验证。若你人工验收时结果不一致，再把现象发给我。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**规则：**
- 前端测试：Agent 可自动执行的启动、构建、接口联通检查必须先自行执行；页面交互验收才交给用户
- 终端测试：Agent 必须先自行运行 curl 或等价接口测试；再给出可复制粘贴的 curl 命令 + 预期返回的 JSON 格式
- curl 命令中的请求体必须与 api-contracts.md 一致
- 预期返回必须与 api-contracts.md 的响应格式一致
- 如果接口需要认证（Bearer Token），先给出获取 token 的 curl，再给出业务接口的 curl

---

### Mock 退出与真实联调（强制）

前端 Mock 只服务于前端 MVP 与契约对齐。每完成一个对应前端页面或 service 的后端业务功能，必须同步更新前端：

1. 确保 `frontend/src/services/` 中该功能在 `VITE_USE_MOCK=false` 时调用真实后端 API
2. 若原先存在 `frontend/src/mocks/` 分支，可以保留为开发演示模式，但不得作为该功能的默认验收路径
3. 移除该功能相关的 `[Mock]` 展示、Mock 账号提示或 Mock-only 文案
4. Tester 必须验证真实请求命中后端接口；可通过浏览器、构建检查、短时服务检查或等价自动化方式证明
5. **禁止**后端业务功能已完成但前端仍停留在 Mock 状态

例外：基础设施、数据库初始化、外部 SDK 客户端封装等没有直接前端入口的底层任务，可以只做后端验收；但如果外部真实密钥/付费资源缺失，只能标记 Mock/fallback 验收通过，不能宣称真实外部能力已验收。

---

### Plan.md 维护规范

`docs/Plan.md` 是唯一的人类可读全局进度文件，设计阶段生成、开发阶段维护。Feature `plan.md` 是实施设计，不记录运行进度；机器状态位于 `.sdd/tasks.json`。

**规则：**
1. Feature 完成后更新全局 Feature 总览中的状态并注明日期
2. 未通过 Feature Spec 全部 AC、Tester 验证和用户门禁，不得标记为“已完成”
3. 内部 Task 状态只更新 `.sdd/tasks.json`，不把 Task 细节复制进全局 Plan
4. 测试证据写入 `.sdd/test-reports/`；全局 Plan 只保留结果和报告链接
5. 开发途中若发现 Feature 边界或 AC 不合理，必须返回阶段 F 更新 Spec；不得只改 tasks.json 掩盖产品定义问题
6. 仅实施顺序变化且不改变 Feature/AC 时，Planner 可以调整任务状态机并同步全局 Plan

---

## 测试纪律（测试库隔离，硬性禁止）

- **测试数据库必须与运行时数据库物理隔离**：`backend/tests/*` 只能使用独立测试库、临时库或事务回滚夹具，禁止直接使用运行时业务库（如 `backend/data/customer_service.db`）。测试代码不得导入运行时 `src.db.session.engine` / `async_session_maker` 后执行 `Base.metadata.drop_all`、`drop_all()` 或等价清表操作。FastAPI 集成测试必须通过 `app.dependency_overrides[get_db]` 注入测试库 session；测试清理只能清理测试库。执行 `python3.11 -m pytest backend/tests --timeout=120` 后，必须确认真实业务库中的核心表和 seed 数据仍存在，防止“测试全绿但联调数据库被清空”。

---

## 交付

全部功能自动验证通过后，输出 `docs/startup.md`（环境要求、启动命令、默认配置）。用户最终业务验收发现问题时，再进入 `sdd-bugfix`。
