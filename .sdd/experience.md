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
