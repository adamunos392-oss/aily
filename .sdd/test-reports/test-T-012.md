# 测试报告：T-012 全系统 E2E 回归验证

**测试时间**：2026-09-21 23:50
**Tester Agent ID**：tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | 工作台依次演示 S-001～S-007，结果与 PRD 一致 | PASS | Playwright `workbench-s001-s007.spec.ts`：差旅表+引用、拒答横幅无引用、会议澄清/消歧/确认后「会议已创建。」、周报可编辑并保留修改、会议室星河 3 号/启航厅且无确认、超时 banner 未知且无「核验成功」、改时间后「原确认已作废」+「请重新确认」15:00 |
| 2 | 单独打开 `/demo/evaluation`，7 条列表与回放正常，标注非产品功能 | PASS | `demo-evaluation.spec.ts` + 浏览器：标题 Demo Validation；横幅「非产品功能」；7 行案例；超时回放「最终未知 · 无会议已创建」；无「会议已创建。」成功句 |
| 3 | 员工工作台左侧仅「对话」；主流程无评测字段；超时场景不出现成功「会议已创建」 | PASS | 侧栏 `.nav-item` 仅「对话」；无「评测与案例」/预期路由/Bad Case；超时断言用精确「会议已创建。」，不把 banner「未确认会议已创建」当成功 |

## technicalChecks 验证

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | `npx playwright test e2e/ --timeout=120000` 通过 | PASS | **9 passed**（16.7s），复用 127.0.0.1:5199 / 8099 |
| 2 | `python3.12 -m pytest backend/tests --timeout=120` 通过 | PASS | **80 passed** |
| 3 | MOCK_MODE=true 下全链路 deterministic 复现 | PASS | `backend/.env` `MOCK_MODE=true`；同一差旅/会议问句稳定命中预置结果 |
| 4 | VITE_USE_MOCK=false 联调端口与 env-policy 一致 | PASS | 前端 `.env`：`VITE_USE_MOCK=false`、`VITE_API_BASE_URL=/api`、代理默认 8099；`vite.config.ts` 可用进程环境覆盖 `VITE_BACKEND_PROXY_TARGET` 切到 8003 |
| 5 | Typecheck / Lint | PASS | `npm run type-check`、`npm run lint` 通过；本任务无 Python 代码变更 |
| 6 | 样式取值与 design-tokens.md 一致 | PASS | 未改 CSS/tokens；壳层沿用已确认工作台与 Demo 页 |

## 环境与规范抽检

- Python 3.12；Agent 端口 5199/8099 在线；`docs/startup.md` 已写用户验收 5175/8003
- 工作台无 `[Mock]`；Demo 页不出现在员工导航
- 无密钥写入报告

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | 超时演示对话会累积历史未知气泡，侧栏 limit=20 可能挤掉该对话 | F-003 演示数据 | 已用 `conv-demo-meeting-timeout` 直达；不必改产品 |
| 2 | Playwright `getByRole('button', { name: '对话' })` 会命中「新建对话」 | E2E 选择器 | 用 `.nav-item` 精确匹配 |
