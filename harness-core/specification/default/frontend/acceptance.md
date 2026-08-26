# 前端验收与节奏（default）

> 来源：原 dev-standards/frontend.md §8/§10/§14 + V8 frontend/acceptance 清单（命令与端口改本集现值）。

## 开发计划（`docs/Plan.md`）

**规范说明**

- `docs/Plan.md` 已在产品设计阶段生成，只维护全局阶段、Feature 交付顺序和人类可读进度，不在前端开发时重建另一套页面计划。
- 页面、视图、Mock 范围和跳转关系来自已确认原型、UI 设计说明书及对应 Feature `spec.md` / `plan.md`。
- 前端 Task 来自 `.sdd/tasks.json`；完成任务后同步全局 Plan 中对应 Feature / 阶段状态，不得修改 Feature 边界或 AC。
- 如果页面实现需要新增 Spec 未定义的用户结果，停止开发并返回产品设计阶段，不得把新需求直接补进 Plan。

**前端开发时允许更新的全局 Plan 信息**

```markdown
## 前端 Mock 验收阶段

- [ ] F-001 对应页面与 Mock 交互通过自动验收
- [ ] F-002 对应页面与 Mock 交互通过自动验收

## Feature 交付总览

| Feature | 用户结果 | 状态 |
|---|---|---|
| F-001 | 用户登录 | Frontend Mock Passed |
```

> 全局 Plan 的完整结构由 `harness-core/skills/sdd-product-design/phase-C.md` 定义；实现细节保留在 Feature Plan，机器状态保留在 `.sdd/tasks.json`。

---

## 开发节奏与推荐顺序

**规范说明**

- **节奏**：基础设施 → 各页用 Mock 完成 → Agent/Tester 自动验收 → 自动进入后端开发。
- **禁止**：把“请用户验收前端”作为进入后端开发的阻塞门禁；只有业务方向不确定、原型明显偏离、或自动验证无法完成时才暂停询问用户。

**示例（节奏）**

```
基础设施（项目初始化、路由、布局）
  → 全部页面开发（Mock 数据）
  → Agent/Tester 自动验收（启动、构建、路由、Mock 数据一致性）
  → 自动进入后端开发
```

**示例（单页实现顺序）**

```
1. 路由配置（含守卫）
2. 页面骨架
3. API Service（可先对接 Mock / 占位）
4. 状态管理（Pinia store）
5. 组件拆分与优化
```

---

## 前端自动验收后的工程约定

**规范说明**

- 前端自动验收通过后，在后端开发阶段使用项目根下（或约定位置）的 **`backend/`** 目录开展后端工作；进度与拆解以 **`docs/Plan.md`** 与仓库结构为准。

（无代码示例。）

---

## 前端验收清单

前端任务自动验收与 Tester 校验时逐条对照（端口取值见 `shared/env-policy.md`）：

- F1 `npm run type-check` 通过
- F2 `npm run lint` 通过
- F3 `npm run build` 通过
- F4 开发服务器可启动（Agent 端口 5199 / 用户验收端口 5175）
- F5 路由跳转正常，受保护页面有守卫
- F6 Mock 数据（如有）集中在 `src/mocks/` 且与 `docs/api-contracts.md` 格式一致，界面带 [Mock] 标识
- F7 页面与已确认原型一致（布局/配色/间距/圆角/字号），偏离须有说明记录
- F8 `baseURL` 来自环境变量，无硬编码后端地址；Vite 已配 `/api`（及 `/ws`，如有）代理
- F9 无组件内直接 axios 调用；401 统一在拦截器处理
- F10 交互五态齐备：抽查交互组件样式表，默认态 + `:hover` / `:active` / `:focus-visible` / `:disabled` 伪类定义齐全（见 style.md 五态条）
- F11 布局结构达标：多栏页面固定视口高度、各栏 `min-height: 0` + 独立滚动；侧栏列表顶部对齐（见 style.md 布局易错点）
