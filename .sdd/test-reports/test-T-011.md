# 测试报告：T-011 F-006 Demo 验证台功能闭环（非产品功能）

**测试时间**：2026-09-21 23:29
**Tester Agent ID**：tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | [AC-F006-01] `/demo/evaluation` 标注 Demo Validation / 非产品功能；列表可见预期/实际路由、通过与否、Bad Case；能区分超时未知与确认失效 | PASS | 横幅「Demo Validation / 非产品功能 · 不是员工工作台，不出现在员工导航」。7 行：超时未知 / 确认失效分列；路由展示为创建会议技能 → 未知、确认作废后重确认 |
| 2 | [AC-F006-02] 点击案例后出现该案事件流，未发生步骤不出现 | PASS | 默认差旅回放：问题改写…最终已回复。选中超时：确认已同意、原子能力超时、结果核验未知、最终未知 · 无会议已创建 |
| 3 | [AC-F006-03] 查看超时/作废回放不产生新的会议已创建，回放无成功节点 | PASS | 超时回放无「会议已创建」成功标题。pytest meetings/confirmations 计数不变 |
| 4 | [AC-F006-04] 连续两次打开列表，7 条覆盖主链且结果一致 | PASS | pytest 两次 GET 体完全相同；覆盖问答/拒答/会议/超时/作废/周报/会议室 |
| 5 | [AC-F006-05] 员工工作台无评测导航与评测字段 | PASS | 侧栏仅「对话」；无「评测与案例」「预期路由」「Bad Case」「案例验证台」 |
| 6 | VITE_USE_MOCK=false 时 Demo 页打真实 `/api/evaluation_cases*`，无 [Mock]；工作台不发起 evaluation_cases | PASS | Demo 页 resource：`/api/evaluation_cases` 与 `/eval-qa-travel`。工作台 clearResourceTimings 后 evaluation_cases=[] |
| 7 | 页面布局、配色与全部文案与 `demo/evaluation.html` 对应 section 一致 | PASS | 标题「案例验证台」、副标题、表头、通过标签、路由对照/事件流回放与原型一致 |

## technicalChecks 验证

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | `python3.12 -m pytest backend/tests/features/f006/ --timeout=120` 通过 | PASS | **6 passed**；全量 `backend/tests` **80 passed** |
| 2 | Typecheck passes | PASS | mypy 98 files Success；`npm run type-check` 通过 |
| 3 | Lint passes | PASS | ruff All checks passed；`npm run lint` 通过 |
| 4 | 样式取值与 design-tokens.md 一致 | PASS | 本任务未改 CSS/tokens |
| 5 | VITE_USE_MOCK=false 时 Demo 页不走 mocks evaluation 分支 | PASS | `evaluation.ts` `isMockEnabled()` 为 false，请求走 `/api` |
| 6 | WorkbenchPage 网络面板无 /api/evaluation_cases | PASS | 工作台 bootstrap 后无该请求 |
| 7 | 回放不触发 API-F003-01；超时 trace 无会议已创建 final 成功节点 | PASS | 只读 GET；final 为「最终未知 · 无会议已创建」 |
| 8 | API 契约 API-F006-01/02 | PASS | total=7；未知 case_id 404「评测案例不存在」 |

## 环境与规范抽检

- Python 3.12；uvicorn `127.0.0.1:8099` 已用当前代码重启
- 分层：Route → EvaluationService → EvaluationRepository + EvaluationAdapter
- 回放不写 knowledge / meetings
- 无密钥写入报告

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | Vite 仍打包 `mocks/evaluation.ts`（service 里 mock 分支 import） | 前端 mock 开关 | 运行时未调用；可后续动态 import |
