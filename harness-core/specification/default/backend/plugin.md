# PyCore Plugin 层规范（default）

> 来源：原 dev-standards/backend-plugin.md 原样迁移；外部服务调用安全条款消双写至 `shared/security.md`（本件留指针）；「深入阅读」节删除（指 pycore/docs，与禁读矛盾）。

> **仅用于 AI Agent 应用。** 普通业务系统不需要 Plugin 层。

## 架构选择

| 应用类型 | 调用链 |
|---------|--------|
| 普通业务系统 | Router → Service → Repository |
| AI Agent 应用 | Router → PluginRegistry → Plugin → Service |

## BasePlugin 速查

```python
from pycore.plugins import BasePlugin, PluginResult
from pycore.core import get_logger

logger = get_logger()  # 模块级！BasePlugin 没有内置 logger

class SearchPlugin(BasePlugin):
    name: str = "search_knowledge"
    description: str = "Search the knowledge base"
    parameters: dict = { ... }  # OpenAI function calling JSON Schema

    async def execute(self, query: str, limit: int = 5, **kwargs) -> PluginResult:
        # **kwargs 是必须的！
        try:
            results = await self._do_search(query, limit)
            return self.success({"query": query, "results": results})
        except Exception as e:
            return self.fail(f"Search error: {e}")
```

## PluginResult 速查

```python
result = PluginResult.ok(data)      # 成功
result = PluginResult.fail("msg")   # 失败

if not result:          # 用 __bool__ 判断
    msg = result.error  # 失败用 .error
else:
    data = result.data  # 成功用 .data
```

## PluginRegistry 速查

```python
registry = PluginRegistry()
registry.register(SearchPlugin())
result = await registry.execute("search_knowledge", query="Python")
specs = registry.to_specs()  # OpenAI function calling 格式
```

## 易错点

| 错误写法 | 正确写法 |
|---------|---------|
| `if not result.success:` | `if not result:` |
| `result.output`（取错误时）| `result.error` |
| `self.failure("msg")` | `self.fail("msg")` |
| `async def execute(self, x):` | `async def execute(self, x, **kwargs):` |
| `len(registry._plugins)` | `len(registry)` |

## 外部服务调用规则（强制）

### 写解析逻辑前必须先真实调用

封装第三方 API 时，必须先写探索代码真实调用并打印响应，确认结构后再写解析逻辑：
```python
# 探索阶段
response = await client.post(url, json=payload, headers=headers)
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
# 确认结构后，再写正式解析代码
```

### 安全红线（指针）

- 百炼禁官方 SDK、`trust_env=False`、禁止继承环境变量：单一权威源在 `shared/security.md`「外部服务调用红线」，本件不重复展开。
