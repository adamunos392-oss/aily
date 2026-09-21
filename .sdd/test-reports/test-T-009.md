# 测试报告：T-009 F-003 创建会议 Skill 功能闭环

**测试时间**：2026-09-21 23:02
**Tester Agent ID**：tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | [AC-F003-01] 用户走完消歧与确认且核验成功，在中栏看到「会议已创建」，右栏事件流含风险/权限、确认、结果核验 | PASS | 点「创建会议」→ 两位张明 →「张明 · 产品部」→ 确认卡 →「同意创建」。中栏「核验成功 / 会议已创建。」及时间/参会人/主题。过程含风险与权限、确认（待确认→已同意）、原子能力、结果核验成功。`POST .../confirmations/.../approve` |
| 2 | [AC-F003-02] 用户发送缺少时间或参会人的创建会议请求，中栏出现澄清追问，不出现会议已创建 | PASS | 发送「帮我跟张明开个会。」中栏「还需要补全会议时间。请问安排在哪一天、几点？」；无确认卡、无「会议已创建」 |
| 3 | [AC-F003-03] 用户提到未指定的张明，中栏出现两名张明的消歧选项，系统不得直接创建 | PASS | 「通讯录里有两位张明，请选择具体的人：」+「张明 · 产品部」「张明 · 财务部」；pytest meetings=0 |
| 4 | [AC-F003-04] 槽位已齐且确认单待确认时，用户未点同意前，中栏不得出现会议已创建 | PASS | 确认卡「请确认创建会议」15:00 / 张明（产品部）、林小北 / 项目复盘会 / 60 分钟 / 线上会议；最终「待确认 · 尚未创建」。pytest pending 时 meetings=0 |
| 5 | [AC-F003-05] 用户已确认 14:00 会议后将时间改为 15:00，旧确认作废，出现针对新时间的新确认卡，新确认同意前不得创建成功 | PASS | pytest + live `PATCH /slots`：14:00 pending → 15:00 新 confirmation_id；旧单 approve 409；meetings=0 |
| 6 | [AC-F003-06] 用户在 MEETING_TIMEOUT_DEMO_CONVERSATION_ID 预置对话确认创建后，中栏与事件流均为未知/待核验，不出现「会议已创建」 | PASS | live `conv-demo-meeting-timeout` approve 后 `status=unknown` `meeting_unknown`，文案为保留信息句；final「未知 · 待核验」；meetings 无新行 |
| 7 | [AC-F003-07] 用户从「执行任务」快捷入口发起约张明开会，后续澄清、确认与成功/失败规则与自然语言创建会议相同 | PASS | 「执行任务」预选产品部张明，直接确认卡（同自然语言确认字段）；pytest shortcut_task approve 后 meeting_success 且 meetings=1 |
| 8 | VITE_USE_MOCK=false 时 turns 与 confirmations 请求命中真实后端，页面无 [Mock] 标记 | PASS | performance 含 `/turns` 与 `/confirmations/.../approve`；场景下拉 disabled；body 无 `[Mock]` |
| 9 | 页面布局、配色与全部文案与会议相关锚点 section 一致 | PASS | 澄清/消歧/确认卡/成功/未知文案与 `01-workbench.html` 对应 section 一致；壳层沿用 T-001 tokens |

## technicalChecks 验证

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | `python3.12 -m pytest backend/tests/features/f003/ --timeout=120` 通过 | PASS | **7 passed**；全量 `backend/tests` **65 passed** |
| 2 | Typecheck passes | PASS | mypy 79 files Success；`npm run type-check` 通过 |
| 3 | Lint passes | PASS | ruff All checks passed；`npm run lint` 通过 |
| 4 | 样式取值与 design-tokens.md 一致 | PASS | 本任务未改 CSS/tokens |
| 5 | VITE_USE_MOCK=false 时不走 mocks 创建会议分支 | PASS | `confirmation.ts` / `turn.ts` `isMockEnabled()` 为 false |
| 6 | 超时路径 meetings 表无新行；unknown 轮次 assistant 文案不含「会议已创建」 | PASS | timeout 助手正文为保留信息句；final 无成功句；pytest meetings=0 |
| 7 | API 契约 API-F002-01/02、API-F003-01/02/03 | PASS | 空 updates 400；非 pending approve 409；turn_id 不匹配 400；GET 快照与 POST 一致 |

## 环境与规范抽检

- Python 3.12.14；uvicorn `127.0.0.1:8099` 已用当前代码重启
- 分层：Route → ConfirmationService / TurnService → SkillService → Mock Adapter
- f003 使用独立 tmp 库；pytest 后运行时 `meeting_rooms` 种子仍在
- 无密钥写入报告

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | 侧栏 `limit=20` 时「会议超时演示」可能被新对话挤出列表 | F-001 列表 | 用 `MEETING_TIMEOUT_DEMO_CONVERSATION_ID` 直达；后续可做置顶或搜索 |
| 2 | 真实编排含改写/记忆等，比原型步骤多 | BR-013 | 保留真实节点 |
| 3 | 场景条仍有「会议已创建」选项（disabled） | T-001 场景条 | 非本轮产品中栏 |
