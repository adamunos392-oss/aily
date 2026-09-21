# 测试报告：T-003 后端脚手架、配置与 Mock 身份

**测试时间**：2026-09-21 17:05
**Tester Agent ID**：tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | `backend/src/main.py` 使用 pycore.api.APIServer，非自建 FastAPI 实例 | PASS | `main.py` 使用 `APIServer(APIConfig(...))`，`app = server.app`；源码无 `FastAPI(`；`test_health.py` 断言 `server.app is app` |
| 2 | `backend/src/core/config.py` 使用 pycore.core.ConfigManager，敏感项从 .env 读取，无硬编码密钥 | PASS | `ConfigManager` + `DotEnvFileLoader`，`load(..., use_env=False)`；`secret_key: str` 无默认值且校验非空；`.env`/`.env.example` 均含 `SECRET_KEY` 字段（未复述值）；业务 md/json 无密钥泄露 |
| 3 | `backend/src/api/deps.py` 基于 pycore 模板扩展，`get_current_user` 注入固定 Mock UserContext | PASS | `get_current_user` 返回固定林小北｜产品部；`get_db` 来自 `src.db.session`；pytest `test_get_current_user_returns_mock_linxiaobei` 通过 |
| 4 | CORS 中间件已注册，允许 Agent 前端 5199 与用户验收 5175 来源 | PASS | `APIConfig.cors_origins=settings.cors_origins`；`CORSMiddleware in app.user_middleware`；真实 uvicorn 下 Origin `5199`/`5175` 均返回对应 `access-control-allow-origin` |
| 5 | `GET /health` 返回 200 | PASS | pytest `test_health_returns_200`；真实启动 `cd backend && PYTHONPATH=.. ./.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8099` 后 `curl /health` → 200，`{"status":"healthy","version":"1.0.0"}` |
| 6 | `python3.12 -m ruff check backend/src backend/tests` 与 `python3.12 -m mypy backend/src backend/tests` 通过 | PASS | 使用 `backend/.venv/bin/python`（3.12.14）：ruff All checks passed；mypy Success: no issues found in 16 source files |

## technicalChecks 验证

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | `python3.12 -m pytest backend/tests --timeout=120` 通过 | PASS | 16 passed（pytest-timeout 在位；`--collect-only` 无 ERROR） |
| 2 | uvicorn 短时启动 | PASS | 端口 8099 短时启动成功并验证后已关闭 |
| 3 | `pycore/` 未纳入项目业务代码质量门禁 | PASS | `pyproject.toml` 中 ruff `exclude` / mypy `exclude` 含 `pycore`；门禁命令仅覆盖 `backend/src` `backend/tests` |
| 4 | 不硬编码密钥；SECRET_KEY 仅来自 .env | PASS | 源码无硬编码密钥字面量；`SECRET_KEY` 由 `.env` 加载 |

## 环境与隔离抽检

- Python：`backend/.venv/bin/python` → 3.12.14（非系统 3.9.6）
- 测试隔离：`backend/tests` 无对运行时 `engine`/`async_session_maker` 的 `drop_all`
- 规范：`rules_files` 解析至 `harness-core/specification/default/...` 存在；分层与 pycore 底座用法符合 tech-stack / layers

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | `db/models.py` 仅有 `Base`，无业务表与 seed | T-004 | 由 T-004 实现 |
| 2 | 无 conversations / identity 业务路由 | T-006 | 由后续任务实现 |
| 3 | 无 PluginRegistry / Mock Adapter | T-005 | 由后续任务实现 |
