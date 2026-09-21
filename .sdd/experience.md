# 项目经验

> 当前项目长期有效的经验。  
> Developer / Tester / Bugfix 在任务完成后维护本文件。

---

## Harness 系统经验摘要

新项目开始时，Developer / Tester / Bugfix 需要同时参考：

- 当前项目经验：`.sdd/experience.md`
- 系统级经验：`<SDD_V6>/memory/harness-experience.md`

---

### T-001: 员工对话工作台前端 Mock（/）
- **陷阱**：`specification/default/frontend/mock.md` 要求界面 Mock 数据带 `[Mock]` 前缀，但原型 `01-workbench.html` 与 AC-F001-04 身份文案是「林小北｜产品部」，后续闭环任务又要求页面无 `[Mock]` 标记。差旅表格/引用/拒答问句以原型为准，与 `api-contracts.md` 示例里的 P6/P7 及 tech-spec `KNOWLEDGE_REFUSE_DEMO_QUERY`（公司上市时间表）不一致。
- **经验**：工作台视觉与文案以 `docs/prototypes/01-workbench.html` + `design-tokens.md` 为唯一权威；`[Mock]` 标识落在原型场景条「原型场景切换（非产品功能）」，不改身份/消息文案。拒答 Mock 同时识别原型问句「下季度期权行权价是多少？」与 config 问句「公司上市时间表是什么？」。事件中文标题用原型「知识检索 / 最终结果」，不用契约示例里的「知识召回 / 完成」。员工导航只有「对话」，`/demo/evaluation` 仅场景条外链，本任务不实现评测页。
- **避坑**：Mock 内部实体可以超集，handler 必须按 endpoint 显式 map DTO；`ConversationDetailResponse` 用 `active_slot_state`（不要用 tech-spec 新建接口草稿里的 `slot_state`）。侧栏时间按 Asia/Shanghai 格式化为「今天 HH:mm」，seed 的 UTC 要能算出原型的 10:24 / 09:49 / 09:12 / 08:40。aily 目录原先只有残缺 `.git`，Git 会误用 Harness 根仓库，需在项目目录 `git init -b main` 成独立仓库。

### T-002: Demo 验证台前端 Mock（/demo/evaluation）
- **陷阱**：API-F006 示例路由是「技能 create_meeting / 技能 generate_work_report」，原型 `demo/evaluation.html` 表格文案是「创建会议技能 / 生成工作周报技能」；Bad Case 契约枚举是 `none` 等，原型展示「无 / 无依据拒答 / 超时未知 / 确认失效」。超时回放原型句「最终未知 · 无会议已创建」含「会议已创建」子串，但不是成功节点。
- **经验**：列表/详情 Mock 按 API-F006-01/02 显式 map DTO（路由字符串用契约示例值）；页面展示用 `evaluationRouteLabel` / `evaluationBadCaseLabel` 对齐原型。事件 `title_zh` 用原型回放句。空态只渲染「暂无预置案例。不得伪造通过率。」，不造通过率。`meta.isDemoValidation=true`，本页不挂员工侧栏；工作台仅场景条外链进入，侧栏不加评测导航。
- **避坑**：超时/作废回放不得出现「会议已创建」成功节点。不要把 evaluation_cases 写进 Vue 或工作台 store。场景条「打开 Demo 验证」依赖本路由，缺路由会 404。

### T-002: Demo 验证台 Vue Router hash 漏写 #（第 1 次返工）
- **陷阱**：`setHash` 早退已用 `route.hash === \`#${scene}\``，但 `router.replace({ hash: scene })` 未带 `#`。Vue Router 4 会把无 `#` 的 hash 拼进 path，场景切换把 `/demo/evaluation#cases` 变成 `/demo/evaluationcase-timeout`。原生 `location.hash = v` 会自动补 `#`，两者不等价。
- **经验**：场景条写 hash 一律 `router.replace({ hash: \`#${id}\` })`。修复后下拉「选中超时案例」「列表空」、点击超时行，pathname 必须仍是 `/demo/evaluation`，hash 为 `#case-timeout` / `#cases-empty`。
- **避坑**：对照 `route.hash` 时记得浏览器 hash 带 `#`；replace 入参也必须带 `#`。本轮为首次返工，非连续同类失败。系统级经验已在 `memory/harness-experience.md`「2026-09-21｜Vue Router hash 必须带 # 前缀」，无需新增回传。

### T-001: TracePanel 来源/过程文案裁剪（第 1 次返工）
- **陷阱**：`section.replace(/ .+$/, "")` 从「第」后第一个空格切掉「3.2 条」；`summary.replace(/\u3000?只读|\u3000?写入/g, "")` 吃掉「写入操作」「只读查询」词内字，再叠标签变成「查询只读」。
- **经验**：相关来源按原型拼 `document_title + 第 X.Y 条 + "：" + excerpt`，只去掉「条」后描述。过程摘要仅剥句尾 `\u3000(?:只读|写入)$`，只读/写入标签也只在该尾标存在时渲染，不按 `includes` / `payload.operation_type` 误标。
- **避坑**：对齐原型的字符串裁剪必须带句尾或「条」锚点，先用原型原文自测再提交。本轮为首次返工，非连续同类失败；系统级经验已存在于 `memory/harness-experience.md`「2026-09-21｜过程/来源文案裁剪正则过宽破坏原型原文」，条目已覆盖 How to apply，无需新增回传。

### T-003: 后端脚手架、配置与 Mock 身份
- **陷阱**：pycore `ConfigManager` 默认只有 TOML loader，且 `load(..., use_env=True)` 会读进程环境；直接 `config.load(AppSettings, "backend/.env")` 会报 No loader。`Logger.configure` 必须在 `get_logger()` 之前，否则 session 模块级 logger 会用默认配置锁死。
- **经验**：在项目 `core/config.py` 用 `DotEnvFileLoader`（`dotenv_values`，不读 `os.environ`）`register_loader` 后 `load(..., use_env=False)`。`main.py` 只用 `pycore.api.APIServer`；`GET /health` 来自 APIServer 内置，不必自建。`get_current_user` 返回 config 中的林小北｜产品部，无 JWT。业务表/Plugin/conversations API 留给后续任务。
- **避坑**：质量门禁只跑 `backend/src` 与 `backend/tests`，不要 `ruff/mypy/pytest` 扫 `pycore/`。venv 用 `python3.12 -m venv backend/.venv`，命令统一 `python3.12`。`.env.example` 与 `.env` 键一一对应；VITE_* 留在 `frontend/.env`，不要混进后端。

### T-004: SQLite 数据库模型与种子数据
- **陷阱**：`cd backend && PYTHONPATH=.. python3.12 scripts/init_db.py` 时 `sys.path[0]` 是 `scripts/`，项目根只有 `pycore` 没有 `src`。测试若对运行时 `engine` 做 `drop_all` 会清掉 `backend/data/aily.db` 的 seed。
- **经验**：脚本把 `backend/` 插入 `sys.path` 后用 `src.*` 导入。`create_all_tables(bind)` 与 `seed_database(session)` 接受外部引擎/会话，测试用 `tmp_path` 独立库。seed 按业务 ID upsert，可重复执行；超时演示对话只 upsert 那一行，不插 meetings。差旅限额/职级/城市写进 knowledge excerpt，拒答问句不得出现在 is_active 条目中。
- **避坑**：质量门禁用 `backend/.venv/bin/python` 从项目根跑 ruff/mypy/pytest；mypy 必须带上项目 `pyproject.toml` 的 exclude，不要对 pycore 绝对路径做 mypy。真实库落盘后再跑 pytest，确认 12 张表和 seed 还在。

### T-005: Agent PluginRegistry 与 Mock Adapter 基础设施
- **陷阱**：`src.services.__init__` 若 re-export `AgentOrchestratorService`，会形成 `plugins.registry → plugins.nodes → services.agent_nodes → services.__init__ → agent_orchestrator → plugins.registry` 循环导入，TestClient 收集阶段即失败。
- **经验**：Plugin 经 Service 调 Adapter；Orchestrator 只按固定名单 `execute`，不要用 `to_specs()` 做开放规划。READ 分支跳过 `risk_permission`，且 adapter/编排都不得追加 `confirmation` 节点。`register_agent_plugins` 必须幂等，否则多个 TestClient startup 会 PluginError。
- **避坑**：质量门禁用 `backend/.venv/bin/python`；mypy 异构 Plugin 列表要标 `list[BasePlugin]`。静态检查「未引入开放规划」只扫 `import/from langgraph|langchain`，不要扫中文禁令注释。
