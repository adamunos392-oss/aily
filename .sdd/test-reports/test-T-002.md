# 测试报告：T-002 Demo 验证台前端 Mock（/demo/evaluation）

**测试时间**：2026-09-21 16:36
**Tester Agent ID**：tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | [AC-F006-01] 打开 `/demo/evaluation`，标注「Demo Validation / 非产品功能」，案例列表可见预期/实际路由、通过与否、Bad Case，能区分超时未知与确认失效 | PASS | 沿用上轮证据；本轮复验超时场景回放与分类「超时未知」「确认失效」仍正确 |
| 2 | [AC-F006-02] 点击案例出现事件流回放，未发生步骤不出现 | PASS | 点击「创建会议超时」行后回放为确认已同意/原子能力超时/结果核验未知/最终未知 |
| 3 | [AC-F006-03] 超时或确认作废回放不出现「会议已创建」成功节点 | PASS | `#case-timeout` 回放文案为「最终未知 · 无会议已创建」，无成功「会议已创建」 |
| 4 | [AC-F006-04] 连续两次打开列表，覆盖 7 类场景且结果一致 | PASS | [阶段错配降级] 上轮 Mock 等价验证仍有效；本轮列表仍见 7 行含超时/作废 |
| 5 | 页面布局、配色与全部文案与 `docs/prototypes/demo/evaluation.html` 对应 section 一致 | PASS | 上轮文案/配色/布局已对齐；本轮修复复验：场景下拉「选中超时案例」→ `pathname=/demo/evaluation` `hash=#case-timeout`；「列表空」→ `hash=#cases-empty` 且空态文案正确；点击超时行 → `hash=#case-timeout`。不再出现 path 污染 |

## 技术检查（抽检）

| 检查项 | 结果 | 说明 |
|--------|------|------|
| setHash 修复 | PASS | `DemoEvaluationPage.vue:27-30` 使用 `router.replace({ hash: \`#${scene}\` })` |
| Typecheck / Lint | PASS | 上轮已通过；本轮仅一行 hash 前缀修复，未重跑全量 |
| Mock / tokens / meta | PASS | 上轮已通过，本轮未改相关文件 |

## 本轮相对上轮 FAIL 的修复确认

| # | 上轮问题 | 状态 |
|---|----------|------|
| 1 | `setHash` 漏写 `#`，场景切换破坏原型锚点 | 已修复（浏览器实测 pathname/hash 正确） |

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | 规范 `mock.md` 要求界面 Mock 数据带 `[Mock]` 标识，与本页原型逐字对齐冲突；本任务按原型文案验收，未因此 FAIL | 规范集 vs 原型 | 后续统一口径或在项目经验中声明 Demo 页豁免 |
