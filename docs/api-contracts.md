# API 契约

> 接口按 Feature 业务动作组织。路由、请求/响应模型、错误码、资源词以已确认的 `docs/tech-spec.md` §3 为权威，本文补齐 Feature/AC 追踪、鉴权、幂等与数据影响。编号沿用 tech-spec。

## 0. 通用契约

### 0.1 成功 / 错误信封

统一 pycore 信封（`specification/default/backend/api-design.md`）：

```json
{
  "code": 200,
  "message": "ok",
  "data": {}
}
```

失败：

```json
{
  "code": 404,
  "message": "对话不存在",
  "data": null
}
```

`code` 为 HTTP 语义整数；业务错误码同时体现在 HTTP 状态与 `message`。tech-spec 所列错误码与 HTTP 映射：

| 业务错误码 | HTTP | 含义 |
|---|---|---|
| 成功 | 200 | `code` 为 200，`data` 为对应响应模型 |
| `VALIDATION_ERROR` | 400 | 参数不合法 |
| `NOT_FOUND` | 404 | 资源不存在或不属于当前身份 |
| `CONFLICT` | 409 | 状态不允许（确认单已作废/已取消/已同意、非会议轮次改槽） |
| `INTERNAL_ERROR` | 500 | 未预期错误 |

禁止 2xx 且 `data` 表示业务失败。禁止成功时 `data` 为 `null`。

### 0.2 鉴权

MVP 无登录。全部 `/api/*` 经 `get_current_user` 注入 Mock UserContext：`user_id=MOCK_USER_ID`（默认 `mock-linxiaobei`）。对话读写必须校验 `conversations.user_id` 等于当前身份，否则 `NOT_FOUND` 或 `CONFLICT`（与 tech-spec 该接口声明一致）。不使用 JWT / Cookie。

### 0.3 幂等

- `POST /api/conversations/{conversation_id}/turns`：若请求带 `client_turn_key` 且同对话已存在相同键，返回原 `TurnResponse`，不新增 turn。
- `POST .../confirmations/{id}/approve` 与 `cancel`：仅 `pending` 可执行；重复调用返回 `CONFLICT`，不得第二次创建 `meetings` 行。
- 其余 GET 天然幂等。`POST /api/conversations` 每次新建一条对话，不幂等。

### 0.4 分页、时间、空值、枚举

- 对话列表：`limit` 默认 `CONVERSATION_LIST_LIMIT`（20），`ge=1, le=100`；评测案例不分页，固定 7 条。
- 时间：响应 datetime 为 ISO-8601 UTC 字符串。
- 空值：JSON `null`；列表空为 `[]`；禁止省略必填键。
- 枚举：与 tech-spec §3.0 / §3.13 逐字一致。

### 0.5 无 API 说明

| AC | 说明 |
|---|---|
| AC-F006-05 | 员工工作台不得调用 `API-F006-01`、`API-F006-02`；由前端路由与页面矩阵保证。无对应员工侧 endpoint。 |

内部 Mock Adapter 规格见 tech-spec §5，不作为前端公开 API。

---

## API-F001-01 获取演示身份

- 来源 Feature：F-001
- 覆盖 AC：AC-F001-04
- 业务动作：工作台展示当前使用者姓名、部门与权限
- Method / Path：GET `/api/identity`
- 权限：Mock UserContext
- 幂等性：是
- 路由文件：`backend/src/api/routes/identity.py`

### 请求

- Path 参数：无
- Query 参数：无
- Request Body：无

### 成功响应

- HTTP 状态：200
- `data`（`IdentityResponse`）：

```json
{
  "user_id": "mock-linxiaobei",
  "display_name": "林小北",
  "department": "产品部",
  "permissions": ["conversation:read", "conversation:write", "knowledge:read"]
}
```

字段取值来自 config `MOCK_USER_ID` / `MOCK_USER_DISPLAY_NAME` / `MOCK_USER_DEPARTMENT`，不读数据库。

### 失败响应

| 场景 | HTTP 状态 | 业务错误码 | 返回内容 |
|---|---|---|---|
| 未预期错误 | 500 | `INTERNAL_ERROR` | `{"code":500,"message":"内部错误","data":null}` |

### 数据影响

- 读取实体：无（config）
- 创建实体：无
- 修改实体：无
- 状态变化：无

---

## API-F001-02 列出最近对话

- 来源 Feature：F-001
- 覆盖 AC：AC-F001-03
- 业务动作：侧栏展示当前身份的最近对话
- Method / Path：GET `/api/conversations`
- 权限：仅返回 `user_id` 等于当前身份的对话
- 幂等性：是
- 路由文件：`backend/src/api/routes/conversations.py`

### 请求

- Query：`limit` integer，可选，默认 config `CONVERSATION_LIST_LIMIT`，范围 1～100

### 成功响应

- HTTP 状态：200
- `data`（`ConversationListResponse`）：

```json
{
  "items": [
    {
      "conversation_id": "conv-001",
      "title": "差旅住宿标准",
      "updated_at": "2026-09-21T06:00:00Z",
      "preview": "公司的差旅住宿标准是什么？"
    }
  ],
  "total": 1
}
```

无对话时 `items` 为 `[]`，`total` 为 0。

### 失败响应

| 场景 | HTTP 状态 | 业务错误码 | 返回内容 |
|---|---|---|---|
| limit 越界 | 400 | `VALIDATION_ERROR` | `{"code":400,"message":"limit 必须在 1 到 100 之间","data":null}` |

### 数据影响

- 读取实体：conversations
- 创建实体：无
- 修改实体：无
- 状态变化：无

---

## API-F001-03 新建对话

- 来源 Feature：F-001
- 覆盖 AC：AC-F001-01
- 业务动作：员工新建独立对话，不携带旧槽位与旧确认单
- Method / Path：POST `/api/conversations`
- 权限：当前身份
- 幂等性：否
- 路由文件：`backend/src/api/routes/conversations.py`

### 请求

- Request Body（`ConversationCreateRequest`）：

```json
{
  "title": null
}
```

`title` 可选；缺省或 `null` 时标题为 `新对话`，首条用户消息发出后可由服务更新标题。

### 成功响应

- HTTP 状态：200
- `data`（`ConversationDetailResponse`）：

```json
{
  "conversation_id": "conv-002",
  "title": "新对话",
  "created_at": "2026-09-21T07:00:00Z",
  "updated_at": "2026-09-21T07:00:00Z",
  "turns": [],
  "active_slot_state": null,
  "active_confirmation": null
}
```

### 失败响应

| 场景 | HTTP 状态 | 业务错误码 | 返回内容 |
|---|---|---|---|
| title 类型错误 | 400 | `VALIDATION_ERROR` | `{"code":400,"message":"title 必须是字符串或 null","data":null}` |
| 未预期错误 | 500 | `INTERNAL_ERROR` | `{"code":500,"message":"内部错误","data":null}` |

### 数据影响

- 读取实体：无
- 创建实体：conversations
- 修改实体：无
- 状态变化：新对话进行中；`active_confirmation` 与 `active_slot_state` 为空

---

## API-F001-04 获取对话详情

- 来源 Feature：F-001
- 覆盖 AC：AC-F001-02
- 业务动作：切换到指定对话，加载该对话轮次、当前槽位与未作废确认单
- Method / Path：GET `/api/conversations/{conversation_id}`
- 权限：仅所属当前身份的对话
- 幂等性：是
- 路由文件：`backend/src/api/routes/conversations.py`

### 请求

- Path：`conversation_id` string 必填

### 成功响应

- HTTP 状态：200
- `data`（`ConversationDetailResponse`）：

```json
{
  "conversation_id": "conv-001",
  "title": "差旅住宿标准",
  "created_at": "2026-09-21T05:00:00Z",
  "updated_at": "2026-09-21T06:00:00Z",
  "turns": [
    {
      "turn_id": "turn-001",
      "role": "user",
      "content": "公司的差旅住宿标准是什么？",
      "status": "replied",
      "created_at": "2026-09-21T06:00:00Z"
    },
    {
      "turn_id": "turn-001",
      "role": "assistant",
      "content": "差旅住宿标准如下。",
      "status": "replied",
      "created_at": "2026-09-21T06:00:01Z"
    }
  ],
  "active_slot_state": null,
  "active_confirmation": null
}
```

切换到另一对话时，响应中的槽位与确认单只属于该 `conversation_id`。

### 失败响应

| 场景 | HTTP 状态 | 业务错误码 | 返回内容 |
|---|---|---|---|
| 对话不存在或不属于当前身份 | 404 | `NOT_FOUND` | `{"code":404,"message":"对话不存在","data":null}` |
| 未预期错误 | 500 | `INTERNAL_ERROR` | `{"code":500,"message":"内部错误","data":null}` |

### 数据影响

- 读取实体：conversations、turns、confirmations（仅 pending）
- 创建实体：无
- 修改实体：无
- 状态变化：无

---

## API-F002-01 发起一轮提问

- 来源 Feature：F-002 / F-003 / F-004 / F-005
- 覆盖 AC：AC-F002-01、AC-F002-02、AC-F002-03、AC-F002-04、AC-F003-02、AC-F003-03、AC-F003-04、AC-F003-07、AC-F004-01、AC-F004-02、AC-F004-03、AC-F005-01、AC-F005-02、AC-F005-03
- 业务动作：在当前对话发出一句输入（含快捷入口预置问句），走固定 Agent 编排，返回本轮结果与事件流
- Method / Path：POST `/api/conversations/{conversation_id}/turns`
- 权限：对话必须属于当前身份
- 幂等性：`client_turn_key` 可选幂等
- 路由文件：`backend/src/api/routes/conversations.py`

### 请求

- Path：`conversation_id` string 必填
- Request Body（`TurnCreateRequest`）：

```json
{
  "content": "公司的差旅住宿标准是什么？",
  "entry_source": "manual",
  "choice_id": null,
  "client_turn_key": "client-turn-001"
}
```

- `content`：必填非空字符串
- `entry_source`：`manual` | `shortcut_knowledge` | `shortcut_meeting` | `shortcut_report` | `shortcut_query` | `shortcut_task`，默认 `manual`
- `choice_id`：消歧/澄清选项，可 `null`
- `client_turn_key`：可 `null`

`entry_source=shortcut_task` 与创建会议同一 `intent=create_meeting` 链（AC-F003-07）。

### 成功响应（S-001 有据问答）

- HTTP 状态：200
- `data`（`TurnResponse`）：

```json
{
  "turn_id": "turn-001",
  "conversation_id": "conv-001",
  "status": "replied",
  "user_message": "公司的差旅住宿标准是什么？",
  "assistant_message": {
    "message_type": "knowledge_table",
    "text": "差旅住宿标准如下。",
    "table_rows": [
      {"level": "P6", "city_type": "一线城市", "limit_cny": 600},
      {"level": "P7", "city_type": "一线城市", "limit_cny": 800}
    ],
    "choices": null,
    "confirmation": null,
    "report_draft": null,
    "rooms": null
  },
  "citations": [
    {
      "document_title": "差旅管理制度",
      "section": "住宿标准",
      "excerpt": "P6 一线城市住宿限额 600 元/晚。",
      "knowledge_entry_id": "know-travel-p6"
    }
  ],
  "route_decision": {
    "route_type": "RAG",
    "target": "enterprise_knowledge",
    "display_route": "企业知识"
  },
  "trace_events": [
    {
      "event_id": "evt-001",
      "turn_id": "turn-001",
      "sequence": 1,
      "occurred_at": "2026-09-21T06:00:00Z",
      "node": "query_rewrite",
      "title_zh": "问题改写",
      "summary": "改写为差旅住宿标准查询",
      "payload": {"rewritten_query": "差旅住宿标准"}
    },
    {
      "event_id": "evt-002",
      "turn_id": "turn-001",
      "sequence": 2,
      "occurred_at": "2026-09-21T06:00:00Z",
      "node": "intent",
      "title_zh": "意图识别",
      "summary": "enterprise_knowledge / READ",
      "payload": {"intent": "enterprise_knowledge", "operation_type": "READ"}
    },
    {
      "event_id": "evt-003",
      "turn_id": "turn-001",
      "sequence": 3,
      "occurred_at": "2026-09-21T06:00:00Z",
      "node": "router",
      "title_zh": "路由",
      "summary": "企业知识",
      "payload": {"route_type": "RAG", "target": "enterprise_knowledge"}
    },
    {
      "event_id": "evt-004",
      "turn_id": "turn-001",
      "sequence": 4,
      "occurred_at": "2026-09-21T06:00:01Z",
      "node": "rag_retrieve",
      "title_zh": "知识召回",
      "summary": "命中 2 条",
      "payload": {"hit_count": 2}
    },
    {
      "event_id": "evt-005",
      "turn_id": "turn-001",
      "sequence": 5,
      "occurred_at": "2026-09-21T06:00:01Z",
      "node": "citation_validate",
      "title_zh": "引用核验",
      "summary": "引用通过",
      "payload": {"valid": true}
    },
    {
      "event_id": "evt-006",
      "turn_id": "turn-001",
      "sequence": 6,
      "occurred_at": "2026-09-21T06:00:01Z",
      "node": "final",
      "title_zh": "完成",
      "summary": "已回复",
      "payload": {"status": "replied"}
    }
  ],
  "intent": {
    "intent": "enterprise_knowledge",
    "operation_type": "READ",
    "confidence": 1.0
  },
  "slot_state": null
}
```

S-001 事件流不得含 `confirmation` 节点。拒答（问句等于 `KNOWLEDGE_REFUSE_DEMO_QUERY`）：`status=refused`，`message_type=refusal`，`citations=[]`。创建会议缺槽：`status=clarifying`，`message_type=clarification`。同名未选定：`message_type=disambiguation` 且 `choices` 至少两项。槽齐写操作：`status=awaiting_confirmation`，`message_type=confirmation`。周报：`message_type=report_draft`。会议室：`message_type=room_list`，无 confirmation。

### 失败响应

| 场景 | HTTP 状态 | 业务错误码 | 返回内容 |
|---|---|---|---|
| 对话不存在 | 404 | `NOT_FOUND` | `{"code":404,"message":"对话不存在","data":null}` |
| content 为空 | 400 | `VALIDATION_ERROR` | `{"code":400,"message":"content 不能为空","data":null}` |
| 对话不属于当前身份 | 409 | `CONFLICT` | `{"code":409,"message":"对话不属于当前身份","data":null}` |

### 数据影响

- 读取实体：conversations、knowledge_entries、people、work_messages、meeting_rooms
- 创建实体：turns、trace_events；有据问答创建 citations；写操作槽齐创建 confirmations；周报创建 report_drafts
- 修改实体：conversations.updated_at / preview / title
- 状态变化：turn 进入 replied / clarifying / awaiting_confirmation / refused 等

---

## API-F002-02 获取单轮详情

- 来源 Feature：F-002 / F-003 / F-004 / F-005
- 覆盖 AC：AC-F002-03、AC-F002-04、AC-F003-04、AC-F003-06、AC-F005-02
- 业务动作：读取本轮完整事件流、引用与助手结果（刷新或右栏回放）
- Method / Path：GET `/api/conversations/{conversation_id}/turns/{turn_id}`
- 权限：对话与轮次属于当前身份
- 幂等性：是
- 路由文件：`backend/src/api/routes/conversations.py`

### 请求

- Path：`conversation_id`、`turn_id` 均为必填 string

### 成功响应

- HTTP 状态：200
- `data`：与 API-F002-01 相同的 `TurnResponse` 形状，字段为该轮已持久化快照。

### 失败响应

| 场景 | HTTP 状态 | 业务错误码 | 返回内容 |
|---|---|---|---|
| 对话或轮次不存在 | 404 | `NOT_FOUND` | `{"code":404,"message":"轮次不存在","data":null}` |

### 数据影响

- 读取实体：turns、citations、trace_events、confirmations、report_drafts
- 创建实体：无
- 修改实体：无
- 状态变化：无

---

## API-F003-01 同意确认单

- 来源 Feature：F-003
- 覆盖 AC：AC-F003-01、AC-F003-04、AC-F003-06、AC-F003-07
- 业务动作：员工同意有效确认单后执行 `create_meeting` Skill 原子 Tool 链
- Method / Path：POST `/api/conversations/{conversation_id}/confirmations/{confirmation_id}/approve`
- 权限：对话属于当前身份
- 幂等性：仅 pending 可成功一次
- 路由文件：`backend/src/api/routes/confirmations.py`

### 请求

- Path：`conversation_id`、`confirmation_id`
- Request Body（`ConfirmationApproveRequest`）：

```json
{
  "turn_id": "turn-010"
}
```

`turn_id` 必填，必须等于确认单绑定轮次。

### 成功响应（会议创建成功）

- HTTP 状态：200
- `data`：`TurnResponse`，`status=replied`，`assistant_message.message_type=meeting_success`，`confirmation.status=approved`，trace 含 `tool_call`（people_lookup、calendar_check、meeting_create 均为 success）与 `result_validate`。

超时演示（`conversation_id` 等于 `MEETING_TIMEOUT_DEMO_CONVERSATION_ID`）：`status=unknown`，`message_type=meeting_unknown`，助手文案不得含「会议已创建」，不写入 meetings 表。

### 失败响应

| 场景 | HTTP 状态 | 业务错误码 | 返回内容 |
|---|---|---|---|
| 确认单或对话不存在 | 404 | `NOT_FOUND` | `{"code":404,"message":"确认单不存在","data":null}` |
| 已作废 / 已取消 / 已同意 | 409 | `CONFLICT` | `{"code":409,"message":"确认单已失效，请重新确认","data":null}` |
| turn_id 不匹配 | 400 | `VALIDATION_ERROR` | `{"code":400,"message":"turn_id 与确认单不匹配","data":null}` |

### 数据影响

- 读取实体：confirmations、turns、people
- 创建实体：meetings（仅 success）；追加 trace_events
- 修改实体：confirmations.status → approved（成功或超时路径均先同意再执行；超时不写 meetings）
- 状态变化：turn → replied 或 unknown

缺槽澄清（AC-F003-02）与同名消歧（AC-F003-03）由 API-F002-01 覆盖，本接口只处理已存在的 pending 确认单。

---

## API-F003-02 取消确认单

- 来源 Feature：F-003
- 覆盖 AC：AC-F003-04
- 业务动作：员工取消写操作，不创建会议
- Method / Path：POST `/api/conversations/{conversation_id}/confirmations/{confirmation_id}/cancel`
- 权限：对话属于当前身份
- 幂等性：仅 pending 可取消一次
- 路由文件：`backend/src/api/routes/confirmations.py`

### 请求

- Request Body（`ConfirmationCancelRequest`）：

```json
{
  "turn_id": "turn-010",
  "reason": null
}
```

### 成功响应

- HTTP 状态：200
- `data`：`TurnResponse`，`status=replied`，`message_type=text`，文案说明已取消，不创建会议；`confirmation.status=cancelled`。

### 失败响应

| 场景 | HTTP 状态 | 业务错误码 | 返回内容 |
|---|---|---|---|
| 不存在 | 404 | `NOT_FOUND` | `{"code":404,"message":"确认单不存在","data":null}` |
| 非 pending | 409 | `CONFLICT` | `{"code":409,"message":"确认单不可取消","data":null}` |

### 数据影响

- 读取实体：confirmations、turns
- 创建实体：追加 trace_events
- 修改实体：confirmations.status → cancelled
- 状态变化：turn → replied；meetings 无新行

---

## API-F003-03 更新关键槽位

- 来源 Feature：F-003
- 覆盖 AC：AC-F003-05
- 业务动作：修改关键槽（至少 `meeting_time`），作废旧确认单并生成新待确认单
- Method / Path：PATCH `/api/conversations/{conversation_id}/turns/{turn_id}/slots`
- 权限：对话属于当前身份
- 幂等性：每次合法更新产生新 confirmation_id
- 路由文件：`backend/src/api/routes/conversations.py`

### 请求

- Path：`conversation_id`、`turn_id`
- Request Body（`SlotUpdateRequest`）：

```json
{
  "updates": {
    "meeting_time": "明天下午 4 点"
  }
}
```

`updates` 至少包含一个键；MVP 必须支持 `meeting_time`。

### 成功响应

- HTTP 状态：200
- `data`：`TurnResponse`，`status=awaiting_confirmation`。旧确认单 `status=invalidated`；新确认单 `status=pending`，摘要含新时间。`trace_events` 含 `confirmation`（invalidated）与 `confirmation`（pending）。

### 失败响应

| 场景 | HTTP 状态 | 业务错误码 | 返回内容 |
|---|---|---|---|
| 轮次不存在 | 404 | `NOT_FOUND` | `{"code":404,"message":"轮次不存在","data":null}` |
| updates 为空 | 400 | `VALIDATION_ERROR` | `{"code":400,"message":"updates 不能为空","data":null}` |
| 非 create_meeting 轮次 | 409 | `CONFLICT` | `{"code":409,"message":"当前轮次不允许修改会议槽位","data":null}` |

### 数据影响

- 读取实体：turns、confirmations
- 创建实体：新 confirmations 行；追加 trace_events
- 修改实体：旧 confirmation → invalidated；turns.slot_state_json
- 状态变化：turn 保持 awaiting_confirmation

---

## API-F004-01 保存周报员工编辑版

- 来源 Feature：F-004
- 覆盖 AC：AC-F004-04
- 业务动作：员工修改本轮周报草稿全文并保存
- Method / Path：PATCH `/api/conversations/{conversation_id}/turns/{turn_id}/report_drafts/{draft_id}`
- 权限：对话属于当前身份
- 幂等性：重复提交以最后一次 `content` 为准
- 路由文件：`backend/src/api/routes/conversations.py`

### 请求

- Path：`conversation_id`、`turn_id`、`draft_id`
- Request Body（`ReportDraftUpdateRequest`）：

```json
{
  "content": "本周完成：需求评审纪要整理。"
}
```

`content` 必填字符串。

### 成功响应

- HTTP 状态：200
- `data`（`ReportDraftResponse`）：

```json
{
  "draft_id": "draft-001",
  "turn_id": "turn-020",
  "content": "本周完成：需求评审纪要整理。",
  "is_edited": true,
  "updated_at": "2026-09-21T08:00:00Z"
}
```

`is_edited` 固定为 `true`。

### 失败响应

| 场景 | HTTP 状态 | 业务错误码 | 返回内容 |
|---|---|---|---|
| 草稿不存在 | 404 | `NOT_FOUND` | `{"code":404,"message":"周报草稿不存在","data":null}` |
| content 缺失 | 400 | `VALIDATION_ERROR` | `{"code":400,"message":"content 不能为空","data":null}` |

### 数据影响

- 读取实体：report_drafts
- 创建实体：无
- 修改实体：report_drafts.content、is_edited=1、updated_at
- 状态变化：草稿进入员工已修改

周报生成（AC-F004-01～03）由 API-F002-01 覆盖，不另设生成接口。

---

## API-F006-01 列出评测案例（Demo 专用）

- 来源 Feature：F-006
- 覆盖 AC：AC-F006-01、AC-F006-04
- 业务动作：Demo 验证台列出预置案例、预期/实际路由、Pass/Fail、Bad Case 分类
- Method / Path：GET `/api/evaluation_cases`
- 权限：Mock UserContext；**仅 `/demo/evaluation` 页面调用**
- 幂等性：是
- 路由文件：`backend/src/api/routes/evaluation_cases.py`

### 请求

- 无 Body / 无筛选（MVP 固定全量）

### 成功响应

- HTTP 状态：200
- `data`（`EvaluationCaseListResponse`）：`total` 必须等于 config `EVALUATION_CASE_COUNT_EXPECTED`（7）。`items` 含下列 `case_id`：`eval-qa-travel`、`eval-qa-refuse`、`eval-meeting-success`、`eval-meeting-timeout`、`eval-meeting-stale`、`eval-report`、`eval-rooms`。每项字段：`case_id`、`name`、`expected_route`、`actual_route`、`passed`、`bad_case_category`。Bad Case 枚举：`none` | `no_evidence_refusal` | `timeout_unknown` | `confirmation_invalidated`。

示例一条：

```json
{
  "items": [
    {
      "case_id": "eval-qa-travel",
      "name": "差旅住宿标准",
      "expected_route": "企业知识",
      "actual_route": "企业知识",
      "passed": true,
      "bad_case_category": "none"
    },
    {
      "case_id": "eval-qa-refuse",
      "name": "无依据问句拒答",
      "expected_route": "企业知识-拒答",
      "actual_route": "企业知识-拒答",
      "passed": true,
      "bad_case_category": "no_evidence_refusal"
    },
    {
      "case_id": "eval-meeting-success",
      "name": "创建项目复盘会",
      "expected_route": "技能 create_meeting",
      "actual_route": "技能 create_meeting",
      "passed": true,
      "bad_case_category": "none"
    },
    {
      "case_id": "eval-meeting-timeout",
      "name": "创建会议超时",
      "expected_route": "技能 create_meeting → 未知",
      "actual_route": "技能 create_meeting → 未知",
      "passed": true,
      "bad_case_category": "timeout_unknown"
    },
    {
      "case_id": "eval-meeting-stale",
      "name": "改时间后重确认",
      "expected_route": "确认作废后重确认",
      "actual_route": "确认作废后重确认",
      "passed": true,
      "bad_case_category": "confirmation_invalidated"
    },
    {
      "case_id": "eval-report",
      "name": "生成本周周报",
      "expected_route": "技能 generate_work_report",
      "actual_route": "技能 generate_work_report",
      "passed": true,
      "bad_case_category": "none"
    },
    {
      "case_id": "eval-rooms",
      "name": "查询可用会议室",
      "expected_route": "只读查询",
      "actual_route": "只读查询",
      "passed": true,
      "bad_case_category": "none"
    }
  ],
  "total": 7
}
```

### 失败响应

| 场景 | HTTP 状态 | 业务错误码 | 返回内容 |
|---|---|---|---|
| 未预期错误 | 500 | `INTERNAL_ERROR` | `{"code":500,"message":"内部错误","data":null}` |

### 数据影响

- 读取实体：evaluation_cases
- 创建实体：无
- 修改实体：无
- 状态变化：无；不创建会议、不写知识

---

## API-F006-02 获取评测案例详情与事件回放

- 来源 Feature：F-006
- 覆盖 AC：AC-F006-02、AC-F006-03
- 业务动作：只读回放预置事件流与路由对照
- Method / Path：GET `/api/evaluation_cases/{case_id}`
- 权限：Mock UserContext；仅 Demo 页调用
- 幂等性：是
- 路由文件：`backend/src/api/routes/evaluation_cases.py`

### 请求

- Path：`case_id` string 必填

### 成功响应

- HTTP 状态：200
- `data`（`EvaluationCaseDetailResponse`）：

```json
{
  "case": {
    "case_id": "eval-meeting-timeout",
    "name": "创建会议超时",
    "scene_id": "S-006",
    "query": "帮我约明天下午 3 点和张明开项目复盘会",
    "expected_route": "技能 create_meeting → 未知",
    "actual_route": "技能 create_meeting → 未知",
    "passed": true,
    "bad_case_category": "timeout_unknown",
    "trace_events": [
      {
        "event_id": "evt-eval-to-1",
        "turn_id": "turn-eval-timeout",
        "sequence": 1,
        "occurred_at": "2026-09-21T09:00:00Z",
        "node": "tool_call",
        "title_zh": "调用会议创建",
        "summary": "超时",
        "payload": {"tool_id": "meeting_create", "status": "timeout"}
      },
      {
        "event_id": "evt-eval-to-2",
        "turn_id": "turn-eval-timeout",
        "sequence": 2,
        "occurred_at": "2026-09-21T09:00:30Z",
        "node": "result_validate",
        "title_zh": "结果核验",
        "summary": "未知",
        "payload": {"status": "unknown"}
      }
    ]
  },
  "route_comparison": {
    "expected_route": "技能 create_meeting → 未知",
    "actual_route": "技能 create_meeting → 未知",
    "passed": true
  },
  "replay_note": "只读回放，不创建会议、不写入企业知识"
}
```

`replay_note` 固定为上述字符串。回放不得调用 API-F003-01。超时案例 `trace_events` 不得含会议已创建的成功 final。

### 失败响应

| 场景 | HTTP 状态 | 业务错误码 | 返回内容 |
|---|---|---|---|
| case_id 未知 | 404 | `NOT_FOUND` | `{"code":404,"message":"评测案例不存在","data":null}` |

### 数据影响

- 读取实体：evaluation_cases（及预置绑定的 trace 快照）
- 创建实体：无
- 修改实体：无
- 状态变化：无
