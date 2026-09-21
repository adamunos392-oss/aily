"""基于 pycore.api.APIServer 的应用入口，禁止自建 FastAPI 实例。"""

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pycore.api import APIConfig, APIServer
from pycore.core import Logger, LoggerConfig, LogLevel, get_logger
from starlette.requests import Request

from src.api.envelope import failure
from src.api.routes import conversations_router, identity_router
from src.core.config import settings
from src.db.session import close_db, init_db
from src.plugins.registry import register_agent_plugins

Logger.configure(
    LoggerConfig(level=LogLevel.INFO, app_name="aily", json_format=False)
)
logger = get_logger()

server = APIServer(
    APIConfig(
        title="Aily企业智能助手",
        version="1.0.0",
        host=settings.host,
        port=settings.port,
        debug=settings.debug,
        cors_origins=settings.cors_origins,
    )
)


async def register_plugins() -> None:
    registry = register_agent_plugins()
    logger.info("Agent Plugin 已注册", plugin_count=len(registry))


server.on_startup(init_db)
server.on_startup(register_plugins)
server.on_shutdown(close_db)

server.include_router(identity_router)
server.include_router(conversations_router)

app = server.app


def _validation_message(exc: RequestValidationError) -> str:
    for err in exc.errors():
        loc = err.get("loc", ())
        msg = str(err.get("msg", ""))
        if "limit" in loc:
            return "limit 必须在 1 到 100 之间"
        if "title" in loc or "title 必须是字符串或 null" in msg:
            return "title 必须是字符串或 null"
    return "参数验证失败"


@app.exception_handler(RequestValidationError)
async def request_validation_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    return failure(400, _validation_message(exc), "VALIDATION_ERROR")


logger.info("后端应用已创建", host=settings.host, port=settings.port)
