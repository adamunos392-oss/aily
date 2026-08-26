# 后端技术栈与框架底座（default）

> 来源：原 dev-standards/backend-dev.md 环境与工具链类硬性禁止 + PyCore 核心配置章 + 首次进入§1 探测详章 + V8 backend/tech-stack 与 logging 条款（pycore 绑定保留，栈值用本集现值）。
> 本件是后端选型、环境与 pycore 用法的单一权威源；开发流程见 workflow.md，分层规范见 layers.md。

## 白名单（固定选型）

- Python 3.11+（Agent 自动探测指令，见「Python 环境与虚拟环境」）
- Web 框架：FastAPI（uvicorn 启动）
- 后端底座：**pycore 框架**（`PYTHONPATH` 引入，禁止 pip 安装，见「pycore 引入方式」）
- ORM：SQLAlchemy（`db/models.py`、`db/session.py`、`api/deps.py` 必须从 pycore 模板复制扩展，见「硬性禁止」）
- 质量工具：项目根 `pyproject.toml`（含 ruff、mypy、pytest 配置），门禁范围收敛为 `backend/src` 与 `backend/tests`

## 选型变更规则

- 白名单外框架/库 = 技术方案偏航，停下报告等拍板。

## 值与选型的单一权威源（方案与代码的关系）

1. 所有技术选型（库/框架/模型/策略）、技术参数（超时/尺寸/阈值/top-k 等）、业务数字（上传大小限制/配额/分页数等）必须在产品设计产物（`docs/Plan.md`、`docs/api-contracts.md`、`docs/data-model.md`）中定义并写死。其中业务数字源自 PRD：需求层写"限制 20MB"。
2. 代码中禁止硬编码上述任何值，一律从 config 读取（pycore `ConfigManager` + `backend/.env`，见本件「ConfigManager 速查」；密钥红线以 `shared/security.md` 为单一权威源，本件不重复展开）。
3. 允许的例外：0/1、空容器字面量、纯结构性常量（如 HTTP 状态码引用）。
4. 正例：`settings = config.settings`，代码用 `settings.port`。反例：代码里 `if len(text) > 500`、`time.sleep(30)`、`"deepseek-v4-flash"` 字符串散落。
5. 验收：grep 代码中的数字字面量与选型字符串，除例外清单外，全部可追溯到产品设计产物或 config 定义。
6. 变更纪律：改任何值 = 改文档 + config，不改代码——代码不含值，改值不动代码。

---

## Python 环境与虚拟环境（首次进入后端开发时执行一次）

Agent 必须先自行探测可用的 Python 3.11+ 指令，不要把这个动作交给用户。

按顺序尝试：

```
python3.11 --version
python3 --version
python --version
```

选择第一个版本号满足 3.11+ 的指令，并记录到 `docs/Plan.md` 的 Python 环境小节。后续**所有命令统一使用该指令**。

只有在以下情况才询问用户：

- 三个候选指令都不存在；
- 存在 Python，但版本低于 3.11；
- 当前命令执行权限不足，Agent 无法完成探测。

探测完成后，Agent 必须自动创建项目内虚拟环境 `.venv` 并安装依赖；不得让用户手动执行项目本地安装命令。如果用户或项目已有指定虚拟环境名称，遵守已有约定；不得修改系统 Python 或全局环境。

```bash
# 示例：Agent 探测到指令为 python3.11
python3.11 -m venv .venv
source .venv/bin/activate

# 安装依赖（在虚拟环境激活后执行）
python3.11 -m pip install -r requirements.txt

# 启动后端（从 backend/ 目录执行，PYTHONPATH=.. 让 pycore 可导入）
cd backend
PYTHONPATH=.. python3.11 -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8099
```

**注意**：
- 本套规范**使用项目内虚拟环境 `.venv`**，除非项目已有明确约定。
- `pycore` **不通过 pip 安装**，而是通过启动命令中的 `PYTHONPATH=..` 引入（详见本件「pycore 引入方式」）。
- 后续所有启动命令、测试引导中涉及后端启动的地方，**都必须包含 `PYTHONPATH=..`**。

---

## 硬性禁止（环境与工具链类，不得例外）

- **严禁读取、依赖或继承进程环境变量**：后端代码**禁止**通过 `os.environ`、`os.getenv`、`environ` 等方式直接读取业务配置；所有配置（API Key、数据库 URL、端口、LLM 地址等）**必须通过后端配置文件**（如 `backend/.env` + PyCore `ConfigManager` / `BaseSettings`）获取。`ConfigManager.load()` 不得使用进程环境覆盖文件配置，即使显式传入 `use_env=True` 也必须失败。测试开关只能控制“是否运行测试”，不能作为业务配置来源。HTTP 客户端（`httpx`、`openai` 等）初始化时必须显式禁用环境继承，`httpx.Client` / `httpx.AsyncClient` 必须设置 `trust_env=False`，禁止裸 `httpx.get/post` 快捷调用（外部服务调用红线全文见 `shared/security.md`）。
- **严禁自己重写 pycore 已提供的核心模块**：新项目后端**必须基于 pycore 框架开发**，禁止在 `backend/src/core/`、`backend/src/api/` 下自己重写 `config.py`、`server.py`、`logger.py`、`exceptions.py`、`responses.py`、`middleware.py` 等。配置管理使用 `pycore.core.ConfigManager`，服务器使用 `pycore.api.APIServer`，日志使用 `pycore.core.get_logger()`，统一响应用 `pycore.api.responses`。
- **数据库分层骨架必须使用 pycore 模板**：`db/models.py`、`db/session.py`、`api/deps.py` 必须从 `pycore/integrations/db/` 和 `pycore/api/` 复制模板后按需扩展，禁止从零手写 SQLAlchemy 基类或会话管理。
- **业务代码目录固定为 `backend/src`**：后端业务代码统一放在 `backend/src/` 下，如 `backend/src/api/`、`backend/src/services/`、`backend/src/repositories/`、`backend/src/models/`、`backend/src/config/`、`backend/src/utils/`。不得要求项目在 `backend/` 根目录直接创建 `routes/`、`services/`、`repositories/` 等业务目录。（数据访问层目录名统一为 `repositories/`，与 layers.md 一致。）
- **代码质量工具链必须配置且范围收敛**：新项目必须在项目根目录提供 `pyproject.toml`（含 ruff、mypy、pytest 配置），可从 `pycore/pyproject.toml` 复制后调整。项目级质量门禁只覆盖业务代码 `backend/src` 与 `backend/tests`（配置权威在本条；执行命令与提交前检查见 workflow.md「每个功能完成后」）。`pycore/` 是后端框架依赖，不纳入项目任务的 lint/typecheck/test 质量门禁；除非任务明确是维护 pycore 框架，否则不得用 `ruff check .`、`mypy .`、`pytest .` 作为后端验收命令。
- **SQLite 路径必须规范化**：`.env` 可使用 `DATABASE_PATH=backend/data/customer_service.db` 这类项目根相对路径，但生成 SQLite URL 前必须解析为绝对路径，并自动创建父目录（`mkdir(parents=True, exist_ok=True)`），避免在 `cd backend` 真实启动路径下解析成 `backend/backend/...` 或报 `unable to open database file`。（数据库文件与上传目录的落点权威表见 `shared/env-policy.md`「存储落点」。）
- **日志参数禁止与 Logger 接口冲突**：禁止用 `message=` 作为关键字参数传入 `logger.info/warning/error()`，与 Python `Logger.warning(msg, ...)` 第一个位置参数冲突。改用 `api_message=` / `error_msg=` / `detail=`。

---

## PyCore 核心配置（原 backend-core）

### ConfigManager 速查

```python
from pycore.core import ConfigManager, BaseSettings

class AppSettings(BaseSettings):
    debug: bool = False
    secret_key: str  # 必须从 backend/.env 读取，禁止写默认值
    database_url: str = "sqlite+aiosqlite:///./app.db"
    host: str = "0.0.0.0"
    port: int = 8099
    cors_origins: list[str] = [
        "http://localhost:5199",
        "http://127.0.0.1:5199",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ]

config = ConfigManager[AppSettings]()
config.load(AppSettings, "backend/.env")
settings = config.settings
```

> `ConfigManager.load()` 支持直接读取 `backend/.env`，默认 `use_env=False`，不得用进程环境变量覆盖文件配置。不要自行 `os.getenv()` 拼字典再 `load_from_dict()`。`.env` 文件加入 `.gitignore`，项目根目录提供 `.env.example`（要求见 `shared/security.md` 密钥红线）。

### Logger 速查与日志条款

```python
from pycore.core import Logger, LoggerConfig, LogLevel, get_logger

Logger.configure(LoggerConfig(level=LogLevel.INFO, app_name="myapp", json_format=False))
logger = get_logger()
logger.info("Server starting", host="127.0.0.1", port=8099)
```

- BasePlugin **没有**内置 logger → 用模块级 `get_logger()`
- BaseService **有**内置 `self.logger`
- 关键链路日志**一行一条、用中文写明动作与结果**，可 grep、可当验收断言；禁止多行 dump 与纯英文碎片。一条日志读出来就能判断该步骤成败（如「调用百炼接口成功，返回含 choices 字段」）。
- 日志禁止携带真实密钥、Token、用户敏感数据（红线见 `shared/security.md`）；关键链路（请求进出、外部服务调用含响应结构确认、数据库初始化、错误发生点）必须留痕。

### main.py 标准模板

```python
from pycore.core import Logger, LoggerConfig, LogLevel, ConfigManager, get_logger
from pycore.api import APIServer, APIConfig
from src.api.routes.auth import router as auth_router
from src.api.routes.items import router as items_router
from src.db.session import engine, init_db, close_db

Logger.configure(LoggerConfig(level=LogLevel.INFO, app_name="myapp", json_format=False))
logger = get_logger()

server = APIServer(APIConfig(
    title="My Application", version="1.0.0",
    host="127.0.0.1", port=8099, debug=True,
    cors_origins=[
        "http://localhost:5199",
        "http://127.0.0.1:5199",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
))

server.on_startup(init_db)
server.on_shutdown(close_db)
server.include_router(auth_router)
server.include_router(items_router)

app = server.app  # cd backend && PYTHONPATH=.. <python指令> -m uvicorn src.main:app --reload
```

### pycore 引入方式与真实运行路径

`pycore` 与 `backend/` 并列存放在项目根目录下，**不通过 pip 安装**，通过 `PYTHONPATH` 引入：

```
project/
├── pycore/          ← 框架包
├── backend/
│   ├── src/
│   │   └── main.py  ← from pycore.core import ...
│   └── .env
└── frontend/
```

```bash
cd backend
PYTHONPATH=.. <python指令> -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8099
```

**真实运行路径必须可用**：后端服务、初始化脚本、维护脚本必须支持从 `backend/` 目录执行：`cd backend && PYTHONPATH=.. python3.11 ...`。`backend/scripts/*.py` 必须把 `backend/` 作为包根，统一使用 `src.*` 导入；禁止把 `backend/src` 加入 `sys.path` 后使用 `db.*`、`config.*`、`models.*` 等裸导入。涉及 `backend/src/main.py`、`backend/src/db/session.py`、`backend/src/db/models.py`、`backend/scripts/*.py` 的任务，必须做真实路径短时验证，不能只依赖项目根目录下的 pytest。

### 项目结构

```
project/
├── pycore/                     ← 框架包（PYTHONPATH 引入）
├── docs/                       ← 产品设计阶段输出
├── backend/
│   ├── .env
│   ├── src/
│   │   ├── api/deps.py, routes/
│   │   ├── db/models.py, session.py
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── services/
│   │   └── main.py
│   └── tests/
├── frontend/
│   └── src/components/, pages/, stores/, services/, router/
└── docs/
```

### 禁止读取

**禁止读取 `pycore/docs/` 目录下的任何 `.md` 文件。** 这些文档是供人阅读的参考资料，token 量大。模型只需检查文件是否存在，不要打开阅读。
