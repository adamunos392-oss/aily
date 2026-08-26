# 前端 API 调用与联调（default）

> 来源：原 dev-standards/frontend.md §6/§7/§13 + §5 的 vite.config.ts 代理示例与启动命令。端口 / .env / CORS 策略的权威表在 `shared/env-policy.md`，本件只放实操配置与代码。

## API 调用封装

**规范说明**

- 使用 **单一 axios 实例**（如 `services/api.ts`），统一 `baseURL`、`timeout`。
- 在 **请求拦截器** 中附加 Token（若有）。
- 在 **响应拦截器** 中统一处理 401 等；禁止在每个页面重复写一套错误处理。
- 业务接口方法写在 `services/*.ts` 中，**禁止在组件内直接** `axios.get('/...')`。
- `baseURL` **禁止**硬编码 `http://localhost:8000`，须来自 `import.meta.env`。

**示例（`services/api.ts`）**

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
```

---

## 路由与导航守卫

**规范说明**

- 需要登录才能访问的路由，使用 `meta.requiresAuth`（或项目内等价约定）。
- 在 **`router/index.ts`** 的 `beforeEach` 中统一校验；未登录跳转登录页。

**示例（`router/index.ts` 片段）**

```typescript
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else {
    next()
  }
})
```

路由表中为需登录页设置 `meta: { requiresAuth: true }`。

---

## Vite 代理配置

任何需要对接后端 API 的前端项目，**必须**在 `vite.config.ts` 中配置 `/api` 代理（端口取值见 `shared/env-policy.md` 端口表）。

**示例（`vite.config.ts` 必须配置开发代理）**

```typescript
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backendTarget = env.VITE_BACKEND_PROXY_TARGET || 'http://localhost:8099'
  const wsTarget = backendTarget.replace(/^http/, 'ws')

  return {
    server: {
      port: 5199,
      proxy: {
        '/api': {
          target: backendTarget,
          changeOrigin: true,
        },
        '/ws': {
          target: wsTarget,
          ws: true,
          changeOrigin: true,
        },
      },
    }
  }
})
```

**规则**：
- WebSocket 路径 `/ws` 必须单独配置 `ws: true` 代理，禁止前端代码直接写 `ws://localhost:<port>`
- 修改 `vite.config.ts` 或 `.env` 后**必须重启 Vite 开发服务器**才能生效
- Agent / Tester 启动前端时默认使用：`cd frontend && npm run dev -- --host 127.0.0.1 --port 5199`
- 给用户门禁验收时使用：`cd frontend && VITE_BACKEND_PROXY_TARGET=http://localhost:8003 npm run dev -- --host 127.0.0.1 --port 5175`

**示例（代码中读取）**

```typescript
const baseURL = import.meta.env.VITE_API_BASE_URL
```

---

## 常见错误对照

**规范说明**

下列为高频错误，编码与 Review 时对照检查（端口与 .env 策略权威表见 `shared/env-policy.md`）。

**示例（错误 → 正确）**

| 错误写法                         | 正确写法                                       |
|----------------------------------|------------------------------------------------|
| `import.meta.env.API_URL`        | `import.meta.env.VITE_API_URL`（必须 `VITE_` 前缀） |
| 前后端共用同一个 `.env`          | 前后端各自独立 `.env`                          |
| 组件内直接 `axios.get(...)`      | 统一经 `services/` 封装调用                    |
| `baseURL` 写死 `localhost:<port>` | 从 `import.meta.env` 读取                      |
| 每页单独处理 401                 | 在 axios 响应拦截器中统一处理                  |
| `.env` 写完整后端 URL 触发 CORS  | `VITE_API_BASE_URL=/api` + Vite 代理配置       |
| 未配 Vite `/api` 代理            | 必配 `server.proxy['/api']` 指向后端端口       |
| WebSocket 直连 `localhost:<port>` | 配置 `/ws` 代理 + 前端用相对路径               |
