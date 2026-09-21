# 设计取值表（B2 权威）

开发与原型共用本表。色值、字号、圆角、间距以本文件为准，禁止近似值。

---

## 1. 本轮页面范围

| 原型文件 | 页面 | 承载 |
|----------|------|------|
| `01-workbench.html` | 对话工作台（员工产品） | F-001～F-005 |
| `demo/evaluation.html` | Demo 验证台（非产品） | F-006 |
| `index.html` | 原型目录 | 无业务功能 |

与 `docs/ui-design-spec.md` 界面清单一致。

---

## 2. 页面 × 状态清单

### 对话工作台 `01-workbench.html`

| 状态 ID | 必须呈现 | 锚点 |
|---------|----------|------|
| 空对话 | 默认空态 | `#empty` |
| 发送中 | 加载态 | `#loading` |
| 知识有据 | 主路径 | `#qa-success` |
| 知识拒答 | 业务失败/空依据 | `#qa-refuse` |
| 会议缺槽澄清 | 边界 | `#meeting-clarify` |
| 同名消歧 | 边界 | `#meeting-disambiguate` |
| 会议待确认 | 写操作门禁 | `#meeting-confirm` |
| 会议已创建 | 主路径成功 | `#meeting-success` |
| 会议超时未知 | 错误/未知 | `#meeting-timeout` |
| 确认作废重确认 | 边界 | `#meeting-stale` |
| 周报可编辑 | 主路径 | `#report` |
| 会议室有结果 | 主路径 | `#rooms` |
| 会议室无可用 | 空结果 | `#rooms-empty` |

顶栏搜索框：禁用态。交互控件须具备可用 / 禁用 / 悬停 / 按下 / 聚焦。

### Demo 验证台 `demo/evaluation.html`（非产品页面）

| 状态 ID | 必须呈现 | 锚点 |
|---------|----------|------|
| 案例列表 | 默认 | `#cases` |
| 选中超时案例 | 详情 + 回放 | `#case-timeout` |
| 列表空 | 空态（演示入口，正式预置不为空） | `#cases-empty` |

页面必须有「Demo Validation / 非产品功能」标注，无员工左导航。

---

## 3. 取值表

### 色

| Token | 用途 | 色值 |
|-------|------|------|
| `--color-primary` | 主按钮、当前导航、链接 | `#3370FF` |
| `--color-primary-hover` | 主按钮悬停 | `#245BDB` |
| `--color-primary-soft` | 选中会话底、只读软标签 | `#E8F0FF` |
| `--color-bg` | 页面背景 | `#F5F6F8` |
| `--color-surface` | 卡片/栏表面 | `#FFFFFF` |
| `--color-text` | 主文字（Off-Black） | `#18181B` |
| `--color-text-secondary` | 次文字 | `#646A73` |
| `--color-text-muted` | 弱文字 | `#8F959E` |
| `--color-border` | 描边 | `#DEE0E3` |
| `--color-success` | 通过、成功 | `#2EA121` |
| `--color-success-soft` | 成功软底 | `#E6F4EA` |
| `--color-warning` | 警告、待确认 | `#FF7D00` |
| `--color-warning-soft` | 警告软底 | `#FFF3E8` |
| `--color-danger` | 未知、不通过 | `#F54A45` |
| `--color-danger-soft` | 危险软底 | `#FDECEA` |
| `--color-tag-muted-bg` | 只读标签底 | `#F2F3F5` |
| `--color-proto-bar` | 原型场景条（非产品） | `#18181B` |

### 字体

| Token | 值 |
|-------|-----|
| `--font-title` | `"Outfit", "PingFang SC", "Noto Sans SC", sans-serif` |
| `--font-body` | `"Inter", "PingFang SC", "Noto Sans SC", sans-serif` |
| `--track-title` | `-0.04em` |

### 字号 / 字重

| Token | 值 | 用途 |
|-------|-----|------|
| `--text-logo` | 20px / 700 | Logo |
| `--text-title` | 16px / 600 | 栏标题 |
| `--text-body` | 14px / 400 | 正文 |
| `--text-body-medium` | 14px / 500 | 按钮、会话名 |
| `--text-sm` | 12px / 400 | 时间、辅助 |
| `--text-table` | 13px / 400 | 表格 |

### 圆角 / 间距 / 栏宽

| Token | 值 |
|-------|-----|
| `--radius` | 8px（核心组件；全站不超过 12px） |
| `--space-1` | 4px |
| `--space-2` | 8px |
| `--space-3` | 12px |
| `--space-4` | 16px |
| `--space-5` | 24px |
| `--header-h` | 56px |
| `--proto-h` | 36px |
| `--aside-w` | 280px |
| `--trace-w` | 360px |
