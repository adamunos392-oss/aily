# 数据模型

> 物理数据结构的唯一事实来源。每个实体和字段必须能追溯到 Feature 或通用基础设施需求。选型与路径以 `docs/tech-spec.md` 为准：SQLite `backend/data/aily.db`，`DATABASE_PATH`。

## 1. 数据设计原则

- 数据库类型：SQLite 3，单文件 `backend/data/aily.db`（相对 `backend/` 的 `DATABASE_PATH`，启动转绝对路径并创建父目录）
- ID 策略：业务主键使用字符串 ID（`conv-*` / `turn-*` / `cfm-*` / `evt-*` / `draft-*` / `eval-*` / `know-*`）；表内另有自增 `id` 仅作存储序号
- 时间与时区：所有时间戳存 UTC ISO-8601 文本（`YYYY-MM-DDTHH:MM:SSZ`）；展示层按本地时区格式化
- 软删除 / 归档策略：MVP 不删除对话、轮次、确认单、事件；确认单作废改 `status`，不删行
- 审计策略：所有业务表含 `created_at`；可变表含 `updated_at`。不记操作者审计日志表（无登录）
- JSON 列：槽位、事件 payload、权限列表等以 JSON 文本存储，读写经 Pydantic 校验
- 预置数据：知识条目、人员、会议室、工作消息、评测案例在库初始化时 seed；演示身份不落库，来自 config

## 2. 实体总览

| 实体/表 | 业务对象 | Owner Feature | 读写 Feature | 生命周期 |
|---|---|---|---|---|
| conversations | 对话 | F-001 | F-001 写；F-001～F-005 读 | 进行中（MVP 不删除） |
| turns | 一轮提问 | 产生该轮的 Feature | F-002～F-005 写；F-001 读列表；F-006 只读预置 | 处理中 → 已回复 / 待澄清 / 待确认 / 未知 / 已拒答 |
| citations | 引用 | F-002 | F-002 写；F-002 读 | 附在有据回答轮次 |
| confirmations | 确认单 | F-003 | F-003 写；F-001/F-003 读 | 待确认 → 已同意 / 已取消 / 已作废 |
| trace_events | 事件 | 产生该轮的 Feature | F-002～F-005 只追加；F-002～F-006 读 | 追加后只读 |
| report_drafts | 周报草稿 | F-004 | F-004 写读 | 已生成 → 员工已修改 |
| knowledge_entries | 企业知识条目 | 预置 | F-002 只读 | 可用 |
| work_messages | 工作消息 | 预置 | F-004 只读 | 可用 |
| people | 人员（找人原子能力） | 预置 | F-003 只读 | 可用 |
| meeting_rooms | 会议室 | 预置 | F-005 只读 | 可用 |
| meetings | 已创建会议结果 | F-003 | F-003 写；F-003 读核验 | 仅确认且 Tool 成功后存在 |
| evaluation_cases | 评测案例 | F-006 | F-006 只读 | 预置只读 |

不落库对象：演示身份（config：`MOCK_USER_ID` / `MOCK_USER_DISPLAY_NAME` / `MOCK_USER_DEPARTMENT`）；技能与原子能力定义（代码常量 + config Skill ID）。

## 3. 实体定义

### conversations

| 字段 | 类型 | 必填 | 默认值 | 业务含义 | 来源 Feature/AC | 约束 |
|---|---|---|---|---|---|---|
| id | integer | 是 | 自增 | 存储序号 | platform | PK |
| conversation_id | text | 是 | - | 对话业务 ID | F-001 / AC-F001-01 | UNIQUE |
| user_id | text | 是 | config `MOCK_USER_ID` | 所属演示身份 | F-001 / AC-F001-04 | 仅该身份可见 |
| title | text | 是 | `新对话` | 侧栏标题 | F-001 / AC-F001-01 | 可由首条用户消息覆盖 |
| preview | text | 否 | NULL | 侧栏预览摘要 | F-001 / AC-F001-03 | 最近一轮用户句截断 |
| created_at | text | 是 | now UTC | 创建时间 | platform | ISO-8601 |
| updated_at | text | 是 | now UTC | 最近活动时间 | F-001 / AC-F001-03 | 新轮次后更新 |

`MEETING_TIMEOUT_DEMO_CONVERSATION_ID`（默认 `conv-demo-meeting-timeout`）必须作为 seed 行存在，供 S-006 重复进入（AC-F003-06）。

### turns

| 字段 | 类型 | 必填 | 默认值 | 业务含义 | 来源 Feature/AC | 约束 |
|---|---|---|---|---|---|---|
| id | integer | 是 | 自增 | 存储序号 | platform | PK |
| turn_id | text | 是 | - | 轮次业务 ID | F-002 / AC-F002-01 | UNIQUE |
| conversation_id | text | 是 | - | 所属对话 | F-001 / AC-F001-02 | FK → conversations.conversation_id |
| client_turn_key | text | 否 | NULL | 客户端幂等键 | F-002 / AC-F002-01 | 同一 conversation 内 UNIQUE 当非空 |
| role | text | 是 | - | `user` 或 `assistant` | F-001 / AC-F001-02 | 仅两值 |
| content | text | 是 | - | 用户原文或助手主文案 | F-002 / AC-F002-01 | 用户句非空 |
| entry_source | text | 是 | `manual` | 入口来源 | F-002 / AC-F002-01 | 见 tech-spec Literal |
| status | text | 是 | `processing` | 本轮状态 | 领域状态机 | 见下枚举 |
| intent | text | 否 | NULL | 意图枚举 | F-002～F-005 | 见 IntentResult |
| operation_type | text | 否 | NULL | READ 或 WRITE | F-003 / AC-F003-04 | WRITE 才可出确认单 |
| route_type | text | 否 | NULL | RAG / SKILL / READ_TOOL | F-002～F-005 | |
| route_target | text | 否 | NULL | 路由目标 ID | F-002～F-005 | |
| display_route | text | 否 | NULL | 展示用路由名 | F-002 / AC-F002-03 | |
| assistant_message_type | text | 否 | NULL | 助手消息多态类型 | F-002～F-005 | 见 TurnResponse |
| assistant_payload_json | text | 否 | NULL | 表格/选项/会议室等 JSON | F-002～F-005 | 与 message_type 匹配 |
| slot_state_json | text | 否 | NULL | 本轮槽位快照 | F-003 / AC-F003-01 | SlotState |
| memory_state_json | text | 否 | NULL | 模板/语言/篇幅 | F-004 / AC-F004-02 | 不得含工作事实 |
| choice_id | text | 否 | NULL | 消歧选项 | F-003 / AC-F003-03 | |
| created_at | text | 是 | now UTC | 创建时间 | platform | |
| updated_at | text | 是 | now UTC | 状态变更时间 | platform | |

status 枚举：`processing` / `replied` / `clarifying` / `awaiting_confirmation` / `unknown` / `refused`。

业务不变量：用户消息与助手结果可存为同一 `turn_id` 的一对行（`role=user` 与 `role=assistant`），或助手字段挂在同一 turn 的 assistant 行。实现必须保证 `GET` 详情能还原 `TurnResponse`。推荐：一条 turn 记录同时含用户句与助手结果（单行），`role` 对列表拆成两条 `TurnSummary`。

### citations

| 字段 | 类型 | 必填 | 默认值 | 业务含义 | 来源 Feature/AC | 约束 |
|---|---|---|---|---|---|---|
| id | integer | 是 | 自增 | 存储序号 | platform | PK |
| turn_id | text | 是 | - | 所属轮次 | F-002 / AC-F002-01 | FK → turns.turn_id |
| knowledge_entry_id | text | 是 | - | 知识条目 ID | F-002 / AC-F002-01 | FK → knowledge_entries.knowledge_entry_id |
| document_title | text | 是 | - | 文档名 | F-002 / AC-F002-01 | 非空 |
| section | text | 是 | - | 章节 | F-002 / AC-F002-01 | 非空 |
| excerpt | text | 是 | - | 原文片段 | F-002 / AC-F002-01 | 须覆盖答案关键数字 |
| score | real | 是 | - | 召回分 | F-002 / AC-F002-02 | ≥ config `RAG_MIN_SCORE` 才可展示 |
| created_at | text | 是 | now UTC | | platform | |

约束：`status=refused` 的 turn 不得有 citations 行（AC-F002-02）。

### confirmations

| 字段 | 类型 | 必填 | 默认值 | 业务含义 | 来源 Feature/AC | 约束 |
|---|---|---|---|---|---|---|
| id | integer | 是 | 自增 | 存储序号 | platform | PK |
| confirmation_id | text | 是 | - | 确认单业务 ID | F-003 / AC-F003-04 | UNIQUE |
| conversation_id | text | 是 | - | 所属对话 | F-001 / BR-015 | FK |
| turn_id | text | 是 | - | 发起确认的轮次 | F-003 / AC-F003-04 | FK |
| status | text | 是 | `pending` | 确认状态 | F-003 状态机 | pending / approved / cancelled / invalidated |
| meeting_time | text | 是 | - | 会议时间原文 | F-003 / AC-F003-01 | 关键槽 |
| attendees_json | text | 是 | `[]` | 参会人展示名列表 | F-003 / AC-F003-01 | JSON array |
| topic | text | 是 | - | 主题 | F-003 / AC-F003-01 | |
| duration_minutes | integer | 是 | config `MEETING_DEFAULT_DURATION_MINUTES` | 时长 | F-003 | |
| meeting_type | text | 是 | config `MEETING_DEFAULT_TYPE` | online / offline | F-003 | |
| slot_snapshot_hash | text | 是 | - | 槽位指纹 | F-003 / AC-F003-05 | 变更即作废 |
| created_at | text | 是 | now UTC | | platform | |
| updated_at | text | 是 | now UTC | | platform | |

不变量：同一 `conversation_id` 同时最多一张 `status=pending` 的确认单（BR-005）。已作废/已取消不得再 approve（AC-F003-05）。

### trace_events

| 字段 | 类型 | 必填 | 默认值 | 业务含义 | 来源 Feature/AC | 约束 |
|---|---|---|---|---|---|---|
| id | integer | 是 | 自增 | 存储序号 | platform | PK |
| event_id | text | 是 | - | 事件 ID | F-002 / AC-F002-03 | UNIQUE |
| turn_id | text | 是 | - | 所属轮次 | F-002 / AC-F002-03 | FK |
| sequence | integer | 是 | - | 本轮顺序 | F-002 / AC-F002-03 | 同 turn 内 UNIQUE，从 1 递增 |
| occurred_at | text | 是 | now UTC | 发生时间 | F-002 / AC-F002-03 | |
| node | text | 是 | - | 节点枚举 | F-002 / AC-F002-03 | 见 TraceEvent.node |
| title_zh | text | 是 | - | 中文标题 | F-002 / AC-F002-03 | |
| summary | text | 是 | - | 摘要 | F-002 / AC-F002-03 | 截断 ≤ `TRACE_EVENT_DETAIL_MAX_CHARS` |
| payload_json | text | 是 | `{}` | 节点关键字段 | F-002 / AC-F002-03 | 未执行节点不得插入 |

READ 轮次禁止插入 `confirmation` 节点（AC-F002-03、AC-F005-02）。`status=unknown` 轮次禁止插入宣称会议已创建的 final 成功节点（AC-F003-06）。

### report_drafts

| 字段 | 类型 | 必填 | 默认值 | 业务含义 | 来源 Feature/AC | 约束 |
|---|---|---|---|---|---|---|
| id | integer | 是 | 自增 | 存储序号 | platform | PK |
| draft_id | text | 是 | - | 草稿 ID | F-004 / AC-F004-01 | UNIQUE |
| turn_id | text | 是 | - | 所属轮次 | F-004 / AC-F004-01 | FK；一 turn 一草稿 |
| skill_name | text | 是 | `生成工作周报` | 技能展示名 | F-004 / AC-F004-01 | |
| content | text | 是 | - | 正文 | F-004 / AC-F004-01 | 事实 ⊆ 本轮 work_messages |
| is_edited | integer | 是 | 0 | 员工是否改过 | F-004 / AC-F004-04 | 0/1 |
| created_at | text | 是 | now UTC | | platform | |
| updated_at | text | 是 | now UTC | | F-004 / AC-F004-04 | |

### knowledge_entries

| 字段 | 类型 | 必填 | 默认值 | 业务含义 | 来源 Feature/AC | 约束 |
|---|---|---|---|---|---|---|
| id | integer | 是 | 自增 | 存储序号 | platform | PK |
| knowledge_entry_id | text | 是 | - | 条目 ID | F-002 / AC-F002-01 | UNIQUE |
| document_title | text | 是 | - | 文档名 | F-002 / AC-F002-01 | |
| section | text | 是 | - | 章节 | F-002 / AC-F002-01 | |
| excerpt | text | 是 | - | 可引用原文 | F-002 / AC-F002-01 | 差旅表须含职级/城市/限额 |
| city_type | text | 否 | NULL | 城市类型 | F-002 / AC-F002-01 | seed 差旅标准用 |
| level | text | 否 | NULL | 职级 | F-002 / AC-F002-01 | |
| limit_cny | integer | 否 | NULL | 住宿限额元 | F-002 / AC-F002-01 | |
| is_active | integer | 是 | 1 | 是否可召回 | F-002 | 0/1 |

S-002 拒答问句（`KNOWLEDGE_REFUSE_DEMO_QUERY`）不得命中任何 `is_active=1` 条目。

### work_messages

| 字段 | 类型 | 必填 | 默认值 | 业务含义 | 来源 Feature/AC | 约束 |
|---|---|---|---|---|---|---|
| id | integer | 是 | 自增 | 存储序号 | platform | PK |
| message_id | text | 是 | - | 消息 ID | F-004 / AC-F004-01 | UNIQUE |
| user_id | text | 是 | config `MOCK_USER_ID` | 所属人 | F-004 | |
| occurred_at | text | 是 | - | 发生时间 | F-004 / AC-F004-01 | 本周窗口内 |
| kind | text | 是 | - | `work` 或 `chitchat` | F-004 / AC-F004-03 | |
| content | text | 是 | - | 消息正文 | F-004 / AC-F004-01 | |
| is_this_week | integer | 是 | 1 | 是否本周 | F-004 / AC-F004-01 | 0/1 |

周报事实只允许来自 `kind=work` 且本轮 Tool 取到的行（AC-F004-03）。

### people

| 字段 | 类型 | 必填 | 默认值 | 业务含义 | 来源 Feature/AC | 约束 |
|---|---|---|---|---|---|---|
| id | integer | 是 | 自增 | 存储序号 | platform | PK |
| person_id | text | 是 | - | 人员 ID | F-003 / AC-F003-03 | UNIQUE |
| display_name | text | 是 | - | 姓名 | F-003 / AC-F003-03 | 可同名 |
| department | text | 是 | - | 部门 | F-003 / AC-F003-03 | 消歧展示 |
| job_title | text | 否 | NULL | 职位 | F-003 / AC-F003-03 | |

seed 至少两名 `display_name=张明`（`MEETING_DISAMBIGUATION_PERSON_NAME`），分属产品部与另一部门。

### meeting_rooms

| 字段 | 类型 | 必填 | 默认值 | 业务含义 | 来源 Feature/AC | 约束 |
|---|---|---|---|---|---|---|
| id | integer | 是 | 自增 | 存储序号 | platform | PK |
| room_id | text | 是 | - | 会议室 ID | F-005 / AC-F005-01 | UNIQUE |
| room_name | text | 是 | - | 名称 | F-005 / AC-F005-01 | |
| available_from | text | 是 | - | 可用开始 | F-005 / AC-F005-01 | ISO datetime |
| available_to | text | 是 | - | 可用结束 | F-005 / AC-F005-01 | 须晚于 from |
| tomorrow_after_hour | integer | 是 | config `MEETING_ROOM_QUERY_AFTER_HOUR` | 命中「下午 3 点后」过滤 | F-005 / AC-F005-01 | |

### meetings

| 字段 | 类型 | 必填 | 默认值 | 业务含义 | 来源 Feature/AC | 约束 |
|---|---|---|---|---|---|---|
| id | integer | 是 | 自增 | 存储序号 | platform | PK |
| meeting_id | text | 是 | - | 会议 ID | F-003 / AC-F003-04 | UNIQUE |
| conversation_id | text | 是 | - | 来源对话 | F-003 | FK |
| confirmation_id | text | 是 | - | 来源确认单 | F-003 / AC-F003-04 | FK；仅 approved 可创建 |
| topic | text | 是 | - | 主题 | F-003 / AC-F003-04 | |
| meeting_time | text | 是 | - | 时间 | F-003 | |
| attendees_json | text | 是 | - | 参会人 | F-003 | |
| created_at | text | 是 | now UTC | | platform | |

超时路径（S-006）不得插入本表（AC-F003-06）。取消/作废确认不得插入。

### evaluation_cases

| 字段 | 类型 | 必填 | 默认值 | 业务含义 | 来源 Feature/AC | 约束 |
|---|---|---|---|---|---|---|
| id | integer | 是 | 自增 | 存储序号 | platform | PK |
| case_id | text | 是 | - | 案例 ID | F-006 / AC-F006-01 | UNIQUE |
| name | text | 是 | - | 案例名 | F-006 / AC-F006-01 | |
| scene_id | text | 是 | - | S-001～S-007 | F-006 / AC-F006-01 | |
| query | text | 是 | - | 预置问句 | F-006 / AC-F006-02 | |
| expected_route | text | 是 | - | 预期路由 | F-006 / AC-F006-01 | |
| actual_route | text | 是 | - | 实际路由 | F-006 / AC-F006-01 | |
| passed | integer | 是 | 1 | 是否通过 | F-006 / AC-F006-01 | 0/1 |
| bad_case_category | text | 是 | `none` | Bad Case 分类 | F-006 / AC-F006-04 | 四值枚举 |
| replay_turn_id | text | 否 | NULL | 回放绑定的预置轮次 | F-006 / AC-F006-02 | 只读，不触发 WRITE |

行数必须等于 config `EVALUATION_CASE_COUNT_EXPECTED`（7）。员工工作台不得读此表（AC-F006-05）。

## 4. 关系与约束

- 外键：`turns.conversation_id` → `conversations`；`citations.turn_id` / `trace_events.turn_id` / `report_drafts.turn_id` / `confirmations.turn_id` → `turns`；`confirmations.conversation_id` → `conversations`；`meetings.confirmation_id` → `confirmations`；`citations.knowledge_entry_id` → `knowledge_entries`
- 唯一：各业务 ID；`turns.client_turn_key` 在同对话非空时唯一；同对话最多一张 `confirmations.status=pending`
- 状态：turn/confirmation 枚举以外的值禁止写入
- 隔离：查询一律带 `conversations.user_id = MOCK_USER_ID`；切换对话不得复用另一对话的 pending confirmation 或 slot_state
- 并发：同一 confirmation 的 approve/cancel 以行状态为准，非 pending 返回冲突，不二次创建 meeting
- 引用：refused turn 零 citation；有据回答的数字必须能在 citation.excerpt 中找到
- 周报：`report_drafts.content` 的事实句必须能在本轮 `work_message_fetch` 结果中找到；闲聊 kind 不得进入草稿

## 5. 索引与查询依据

| 索引 | 服务查询 | 来源 Feature/AC | 原因 |
|---|---|---|---|
| ux_conversations_conversation_id | 详情/切换 | AC-F001-02 | 按业务 ID 取对话 |
| ix_conversations_user_updated | 最近列表 | AC-F001-03 | `user_id, updated_at DESC` |
| ux_turns_turn_id | 单轮详情 | AC-F002-03 | 取 Trace / 来源 |
| ix_turns_conversation_created | 对话内轮次 | AC-F001-02 | `conversation_id, created_at` |
| ux_turns_conv_client_key | 幂等 | AC-F002-01 | 非空 `conversation_id, client_turn_key` |
| ix_citations_turn | 来源视图 | AC-F002-04 | `turn_id` |
| ux_confirmations_confirmation_id | 同意/取消 | AC-F003-04 | |
| ix_confirmations_conv_status | 当前待确认 | AC-F003-04 | `conversation_id, status` |
| ux_trace_turn_seq | 事件流顺序 | AC-F002-03 | `turn_id, sequence` |
| ux_report_drafts_draft_id | 保存编辑 | AC-F004-04 | |
| ux_knowledge_entry_id | RAG | AC-F002-01 | |
| ux_eval_case_id | Demo 详情 | AC-F006-02 | |

## 6. 数据迁移与兼容性

- 初始建表：应用启动用 SQLAlchemy `create_all` + seed 脚本写入知识/人员/会议室/工作消息/7 条评测案例/超时演示对话
- 变更策略：MVP 无历史用户数据；字段变更允许重建本地 SQLite
- 回滚边界：删除 `backend/data/aily.db` 即可回到空库；seed 必须可重复执行
