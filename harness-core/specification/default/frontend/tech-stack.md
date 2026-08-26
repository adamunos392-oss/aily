# 前端技术栈（default）

> 来源：原 dev-standards/frontend.md §1/§2/§3 + V8 frontend/tech-stack 条款格式（值用本集现值）。选型白名单的单一权威源在本件。

## 总则

**规范说明**

- 开发必须与 **`docs/prototypes/` 下已确认原型**一致：布局、组件位置、配色、间距不得随意发挥；偏离须说明原因并经用户确认。
- 页面结构与信息架构以 PRD + 原型为准，**不可凭感觉改页面规范**。
- 技术栈以本项目规范集声明为准：default 集 = **Vue 3 + TypeScript + Pinia + Vue Router**（本集内不接受无确认替换）。

---

## 白名单（固定选型）

**规范说明**

- 框架：Vue 3（Composition API 推荐）
- 语言：TypeScript
- 构建：Vite
- 状态：Pinia
- 路由：Vue Router
- 请求库：Axios（单一实例经 `services/` 封装，见 api-client.md）

（无单独代码示例。）

## 选型变更规则

- 白名单外技术（其他框架 / UI 库 / 状态库）= 技术方案偏航，停下报告等拍板。

---

## 目录结构

**规范说明**

- 页面放 `pages/`，可复用块放 `components/`，接口放 `services/`，全局状态放 `stores/`，路由放 `router/`，公共类型放 `types/`，工具放 `utils/`。

**示例（目录树）**

```
frontend/src/
├── components/     # 通用组件（AppHeader.vue, UserAvatar.vue）
├── pages/          # 页面级组件（LoginPage.vue, DashboardPage.vue）
├── stores/         # Pinia 状态管理
├── services/       # API 调用封装
├── router/         # 路由配置
├── types/          # TypeScript 类型定义
└── utils/          # 工具函数
```
