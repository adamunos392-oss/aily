# 测试报告：T-005 Agent PluginRegistry 与 Mock Adapter 基础设施

**测试时间**：2026-09-21 20:05
**Tester Agent ID**：tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | PluginRegistry 在 startup 注册全部 Agent 节点 Plugin，编排顺序与 tech-spec §3 一致 | PASS | `main.py` `server.on_startup(register_plugins)` → `register_agent_plugins()`；`AGENT_PLUGIN_NAMES` / `build_agent_plugins()` 顺序为 rewrite→intent→slot→memory→risk_permission→router→rag→skill→read_tool→result_validation；TestClient lifespan 日志 `plugin_count=10`，`list_plugins()` 与 tech-spec §3 一致 |
| 2 | AgentOrchestratorService 固定链路执行，不引入 Planner/ReAct/Multi-Agent | PASS | `agent_orchestrator.py` 固定 `_execute` 顺序；WRITE 才跑 risk_permission；按 route 分支 rag/skill/read_tool；源码与全量 `backend/src` 无 langgraph/langchain 导入（pytest `test_source_has_no_open_planning_frameworks` / `test_orchestrator_source_is_fixed_pipeline`） |
| 3 | `backend/src/repositories/mock/` 含 8 个 adapter，MOCK_MODE=true 时 deterministic 复现 | PASS | 8 文件存在：rewrite/intent/slot/router/rag/tool/skill/evaluation；`settings.mock_mode is True`；同输入两次 `model_dump` 完全一致（`test_same_input_is_deterministic`） |
| 4 | TraceEvent 只追加真实发生节点，READ 场景 adapter 不产出 confirmation 节点 | PASS | 差旅/拒答/会议室 READ 路径 nodes 无 `confirmation`、无 `risk_permission`；WRITE+choice 路径才有 `risk_permission`+`confirmation`；evaluation READ 案例回放无 confirmation |
| 5 | MOCK_MODE、MOCK_DETERMINISTIC_SEED 等 config 键从 AppSettings 读取，无硬编码 | PASS | Orchestrator 读 `settings.mock_mode`；ids/slot/tool 等读 `mock_deterministic_seed`；skill/router/rag/query_rules 等读 AppSettings 键；`SECRET_KEY` 仅来自 `.env`；未发现硬编码密钥 |

## technicalChecks 验证

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | `python3.12 -m pytest backend/tests/test_plugin_registry.py backend/tests/test_orchestrator_skeleton.py --timeout=120` 通过 | PASS | `backend/.venv/bin/python -m pytest ... --timeout=120` → **12 passed**；pytest-timeout 在位；`--collect-only` 无 ERROR |
| 2 | `python3.12 -m ruff check backend/src backend/tests` 通过 | PASS | All checks passed |
| 3 | `python3.12 -m mypy backend/src backend/tests` 通过 | PASS | Success: no issues found in 40 source files |
| 4 | `cd backend && PYTHONPATH=.. python3.12 -m uvicorn src.main:app --host 127.0.0.1 --port 8099` 可短时启动 | PASS | 8099 已被旧进程占用（PID 23825，`/health` 仍 200）；按任务说明改用：① TestClient lifespan（health 200 + 注册 10 plugins）；② `uvicorn` 短时启动于 **18099**，`GET /health` → 200 后关闭。当前代码可短时启动 |

## 环境与规范抽检

- Python：`backend/.venv/bin/python` → 3.12.14（禁止系统 3.9.6）
- 分层：Plugin（`plugins/nodes.py`）→ Service（`services/agent_nodes.py`）→ Mock Adapter（`repositories/mock/*`），符合 plugin.md / layers
- 测试隔离：本轮 T-005 用例为进程内编排，未对运行时库 `drop_all`；既有 `test_init_db` 使用独立 tmp 库
- 无 TODO/FIXME/HACK；无 langgraph/langchain；无密钥泄露

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | 业务 HTTP 路由（identity/conversations/turns 等）尚未注册 | T-006+ | 后续闭环任务实现，不纳入 T-005 |
| 2 | 本机 8099 仍有旧 uvicorn（PID 23825）占用 | 环境 | 不阻塞本任务；后续联调前建议确认进程与当前代码一致 |
