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

### T-006: F-001 对话上下文功能闭环
- **陷阱**：pycore `success_response` 实际字段是 `success/data/error`，aily `api-contracts.md` 与前端 `unwrapEnvelope` 要的是 `{code, message, data}`。`HTTPException(detail=...)` 会被 FastAPI 包成 `{detail: ...}`。`get_db` 若不在 yield 后 commit，POST 新建对话下一请求看不到。
- **经验**：项目内用 `src/api/envelope.py` 调 pycore 再映射扁平信封；在 `main.py` 注册 `RequestValidationError` handler。ConversationRepository 所有查询带 `user_id`。详情里 `active_slot_state` / `active_confirmation` 只取当前 `conversation_id`。`VITE_USE_MOCK=false` 时 identity/conversations 走 `services/*` 真实 `/api`；工作台三栏与原型文案不重写。测试用 `tmp_path` 独立库 + `dependency_overrides[get_db]`。
- **避坑**：不要覆盖 `WorkbenchPage.vue` / `DemoEvaluationPage.vue` 整页。limit/title 校验必须返回 400 与契约原文，不能用 FastAPI 默认 422。8099 上已有 uvicorn 时改用空闲端口做短时启动，不要杀 5199 Vite。

### T-005: Agent PluginRegistry 与 Mock Adapter 基础设施
- **陷阱**：`src.services.__init__` 若 re-export `AgentOrchestratorService`，会形成 `plugins.registry → plugins.nodes → services.agent_nodes → services.__init__ → agent_orchestrator → plugins.registry` 循环导入，TestClient 收集阶段即失败。
- **经验**：Plugin 经 Service 调 Adapter；Orchestrator 只按固定名单 `execute`，不要用 `to_specs()` 做开放规划。READ 分支跳过 `risk_permission`，且 adapter/编排都不得追加 `confirmation` 节点。`register_agent_plugins` 必须幂等，否则多个 TestClient startup 会 PluginError。
- **避坑**：质量门禁用 `backend/.venv/bin/python`；mypy 异构 Plugin 列表要标 `list[BasePlugin]`。静态检查「未引入开放规划」只扫 `import/from langgraph|langchain`，不要扫中文禁令注释。

### T-007: F-002 企业知识问答功能闭环
- **陷阱**：`citations.turn_id` 有外键。Turn 与 Citation 同一 flush 时 SQLite 会 `FOREIGN KEY constraint failed`。
- **经验**：`self.db.add(turn)` 后先 `await self.db.flush()`，再写 citations / trace_events。拒答与有据答案文案、引用 excerpt 按 `01-workbench.html#qa-success/#qa-refuse` 写，不要用契约示例里的短句。
- **避坑**：Mock 关闭后必须真正 `GET /turns/{id}` 填 `turnMap`，否则中栏只有摘要气泡看不到表格。历史夹具轮次没有 payload 时 hydrate 要吞掉 404，不能让 bootstrap 整页失败。

### T-008: F-005 会议室查询功能闭环
- **陷阱**：空会议室验收（AC-F005-03）不能靠新 config 键；对整份 Turn JSON 做「会议已创建」子串断言会误伤原型句「已回复 · 未创建会议」。
- **经验**：空列表用 pytest `monkeypatch.setattr(ToolAdapter, "demo_rooms", lambda self: [])`。中栏文案对齐 `#rooms` / `#rooms-empty`；过程标题用原型「路由 / 原子能力 / 已回复 · 未创建会议」，不要用契约示例里的「完成」。只读查询不得写 confirmations/meetings。
- **避坑**：默认种子仍是星河 3 号 / 启航厅。空结果只测 assistant 正文，不要扫整个 blob。BR-013 保留改写/槽位/记忆/结果核验真实步骤，不按原型 4 步裁掉。

### T-009: F-003 创建会议 Skill 功能闭环
- **陷阱**：create_turn 若不落库 pending confirmation，前端同意会 404。`开会` 不能当成主题，否则「帮我跟张明开个会」不会缺 topic。槽位摘要若先判断同名、再判断缺失，澄清轮会误显示「时间已填」。
- **经验**：pending 确认单在 Turn flush 后写入 confirmations；同意只对 pending 跑 people_lookup→calendar_check→meeting_create。超时对话 ID 走 timeout，不插 meetings。PATCH slots 必须先作废旧 pending（每对话仅一条 pending）。中栏文案对齐 `#meeting-clarify/#meeting-disambiguate/#meeting-confirm/#meeting-success/#meeting-timeout`。
- **避坑**：执行任务快捷入口会带上 `choice_id=person:zhangming-product`，跳过消歧直接待确认，规则仍与自然语言确认/成功相同。侧栏 limit=20 可能挤掉「会议超时演示」，应用 `MEETING_TIMEOUT_DEMO_CONVERSATION_ID` 直达。超时 banner「未确认会议已创建」含子串，不要当成功。

### T-010: F-004 周报生成与编辑功能闭环
- **陷阱**：Skill.plan 若在取消息前写死草稿，monkeypatch 本轮 Tool 结果不会进入正文，AC-F004-02 会 FAIL。GET 若只读 turns.assistant_payload_json，PATCH 后刷新会回到生成稿。
- **经验**：`work_message_fetch` 后再 compose：过滤 `kind=chitchat`，抽取 `kind=work`，套 Memory 的简洁中文事项列表。pending 草稿落 `report_drafts`；PATCH 同时改表与 payload，GET 以表为准。中栏文案对齐 `#report`。记忆 payload 只允许 template_style/language/length。
- **避坑**：周报是 READ，不要 risk_permission/confirmation。侧栏点「生成周报」会发到当前对话，测 AC-01 先「新建对话」。BR-013 保留改写/记忆/过滤/抽取/润色真实步骤，不按原型 4 步裁掉。

### T-011: F-006 Demo 验证台功能闭环
- **陷阱**：会议室回放若用 `confirmation` 节点展示「未出现确认」，会撞上 READ 案例禁止 confirmation 的骨架测试。超时回放标题「最终未知 · 无会议已创建」含子串「会议已创建」，不能当成功节点。
- **经验**：列表读 `evaluation_cases` 表，回放 traces 来自 adapter 快照；GET 详情不得跑 approve / 写 meetings。中栏文案用 `evaluationRouteLabel` / `evaluationBadCaseLabel` 对齐原型，契约路由字符串仍是 `技能 create_meeting`。员工工作台只留场景条外链，不请求 evaluation_cases。
- **避坑**：空列表是原型场景条 `#cases-empty` 的本地态，不要伪造通过率。回放只展示该案真实步骤的 `title_zh`。

### T-012: 全系统 E2E 回归验证
- **陷阱**：工作台 `.empty-hint` 与右栏「本轮尚无过程」同 class；`getByRole('button', { name: '对话' })` 会命中「新建对话」和标题含「对话」的会话。超时 banner「未确认会议已创建」含子串「会议已创建」，不能用 includes 当成功。POST `/turns` 返回后 `sending=false`，表格要等 GET hydrate 才进 `turnMap`。
- **经验**：E2E 用 `.messages .empty-hint`、`.nav-item`、精确文案「会议已创建。」；发消息同时 `waitForResponse` GET `/turns/{id}`。启动文档写清 python3.12、`backend/.venv`、Agent 5199/8099 与验收 5175/8003；Vite 代理必须能被进程环境 `VITE_BACKEND_PROXY_TARGET` 覆盖。
- **避坑**：超时对话不在侧栏前 20 条时用 `MEETING_TIMEOUT_DEMO_CONVERSATION_ID` 直达。不要为 E2E 改员工导航或加评测入口。

