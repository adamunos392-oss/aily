# 测试报告：T-004 SQLite 数据库模型与种子数据

**测试时间**：2026-09-21 17:18
**Tester Agent ID**：tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | `cd backend && PYTHONPATH=.. python3.12 scripts/init_db.py` 执行成功 | PASS | 使用 `backend/.venv/bin/python`（3.12.14）：`PYTHONPATH=.. ./.venv/bin/python scripts/init_db.py` exit 0；日志确认 seed 写入与 `db_path=.../backend/data/aily.db` |
| 2 | 真实 SQLite 文件 `backend/data/aily.db` 存在，全部目标业务表已创建 | PASS | 文件存在（143360 bytes）；12 张业务表均在：conversations / turns / citations / confirmations / trace_events / report_drafts / knowledge_entries / work_messages / people / meeting_rooms / meetings / evaluation_cases |
| 3 | seed 含 knowledge_entries（差旅标准）、people（至少两名 display_name=张明）、meeting_rooms、work_messages（含 work 与 chitchat）、evaluation_cases（7 条）、conversations 含 MEETING_TIMEOUT_DEMO_CONVERSATION_ID 行 | PASS | 真实库查询：knowledge 4 条含 800/600/1200 限额与职级/城市；张明×2（产品部+财务部）；会议室「星河 3 号」「启航厅」；work+chitchat（含「晚上吃啥」）；evaluation_cases=7；`conv-demo-meeting-timeout` 存在且对应 meetings=0 |
| 4 | `backend/src/db/models.py` 与 `session.py` 基于 pycore 模板扩展，DATABASE_PATH 转绝对路径并 mkdir 父目录 | PASS | 字段/索引对照 `docs/data-model.md`；`resolve_database_file` 将相对路径相对 `BACKEND_DIR` resolve 并 `mkdir(parents=True)`；DeclarativeBase + async engine/session 模式与 pycore 模板一致并扩展业务表 |

## technicalChecks 验证

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | `python3.12 -m pytest backend/tests/test_init_db.py --timeout=120` 通过 | PASS | 项目根：`PYTHONPATH=. backend/.venv/bin/python -m pytest backend/tests/test_init_db.py --timeout=120` → **10 passed**；`--collect-only` 无 ERROR；pytest-timeout 在位 |
| 2 | seed 可重复执行（幂等或安全重建） | PASS | pytest `test_seed_is_idempotent` 通过；真实库二次执行 `init_db.py` 后计数不变（knowledge=4, 张明=2, rooms=2, work_messages=3, evaluation_cases=7, timeout_conv=1） |
| 3 | `python3.12 -m ruff check backend/src backend/tests` 通过 | PASS | All checks passed |
| 4 | `python3.12 -m mypy backend/src backend/tests` 通过 | PASS | Success: no issues found in 18 source files |

## 环境与隔离抽检

- Python：`backend/.venv/bin/python` → 3.12.14
- 测试使用 `tmp_path` 独立库（`aily-test.db`），不导入运行时 `engine` 做 `drop_all`
- `session.py` / `seed.py` / `init_db.py` 源码无 `metadata.drop_all`
- pytest 后再查真实 `backend/data/aily.db`：12 表仍在，seed 仍在（evaluation=7、张明=2、timeout 对话=1、knowledge=4）

## 对照 data-model.md

- 12 张业务表字段与索引命名与 `docs/data-model.md` 一致（含 partial unique：client_turn_key、pending confirmation）
- seed 覆盖差旅知识、双张明、会议室、本周 work/chitchat、7 评测案例、超时演示对话；超时路径不插 meetings

## 超出范围发现（不影响当前任务判定）

无（业务 API、PluginRegistry 未纳入本轮判定）。
