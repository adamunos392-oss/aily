# Aily 企业智能助手 — 启动文档

本地演示环境。全程 Mock Adapter（`MOCK_MODE=true`），无登录，默认身份林小北｜产品部。真实 LLM / 飞书 / 日历不接入。

## 环境要求

| 项 | 要求 |
|---|---|
| Python | **3.12**（禁止系统 `python3` 3.9.x） |
| Node.js | 能跑 Vite 6 / npm |
| 虚拟环境 | `backend/.venv`（`python3.12 -m venv backend/.venv`） |
| 数据库 | SQLite `backend/data/aily.db`（相对 `backend/` 解析） |

首次安装：

```bash
cd backend
python3.12 -m venv .venv
.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install -r requirements.txt

cd ../frontend
npm install
npx playwright install chromium
```

## 配置

前后端各自 `.env`，不要混用。从 example 复制后按字段填写，**不要把密钥写进本文档**。

| 文件 | 关键字段 | 默认 |
|---|---|---|
| `backend/.env` | `MOCK_MODE` | `true`（演示必须） |
| `backend/.env` | `PORT` / `HOST` | `8099` / `127.0.0.1` |
| `backend/.env` | `SECRET_KEY` | 已占位于 `backend/.env`，勿提交 |
| `frontend/.env` | `VITE_USE_MOCK` | `false`（走真实后端） |
| `frontend/.env` | `VITE_API_BASE_URL` | `/api`（相对路径，禁止写成完整后端 URL） |
| `frontend/.env` | `VITE_BACKEND_PROXY_TARGET` | `http://localhost:8099` |

改 `.env` 或 `vite.config.ts` 后必须重启对应进程。

## 端口

| 用途 | 前端 | 后端 |
|---|---|---|
| Agent 开发 / 自动验证 | `127.0.0.1:5199` | `127.0.0.1:8099` |
| 用户验收门禁 | `127.0.0.1:5175` | `127.0.0.1:8003` |

## Agent 开发启动

后端（在 `backend/` 目录，把项目根与 `backend/` 都放进 `PYTHONPATH`）：

```bash
cd backend
PYTHONPATH=..:. .venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8099
```

前端：

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5199
```

访问：

- 员工工作台：http://127.0.0.1:5199/
- Demo 验证台（非产品功能）：http://127.0.0.1:5199/demo/evaluation

健康检查：http://127.0.0.1:8099/health

## 用户验收启动

后端改绑 8003（`.env` 的 `PORT` 仍可以是 8099，以 uvicorn `--port` 为准）：

```bash
cd backend
PYTHONPATH=..:. .venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8003
```

前端临时把代理指到验收后端：

```bash
cd frontend
VITE_BACKEND_PROXY_TARGET=http://localhost:8003 npm run dev -- --host 127.0.0.1 --port 5175
```

访问：http://127.0.0.1:5175/ 与 http://127.0.0.1:5175/demo/evaluation

## 默认演示约定

- 身份：林小北｜产品部，无登录
- 员工导航只有「对话」；评测不进员工侧栏
- 超时演示对话 ID：`conv-demo-meeting-timeout`（侧栏最多 20 条时可能被挤出，可直达该 ID）
- 超时未知文案含「未确认会议已创建」，**不是**成功「会议已创建。」

## 验证命令

```bash
# 后端（在项目根，使用 backend/.venv）
backend/.venv/bin/python -m pytest backend/tests --timeout=120

# 前端类型与 lint
cd frontend && npm run type-check && npm run lint

# 全系统 E2E（复用已启动的 5199/8099）
cd frontend && npx playwright test e2e/ --timeout=120000
```
