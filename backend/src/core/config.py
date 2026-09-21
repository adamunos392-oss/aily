"""应用配置：AppSettings + pycore ConfigManager，从 backend/.env 读取。"""

from pathlib import Path
from typing import Any, Literal, cast

from dotenv import dotenv_values
from pycore.core import BaseSettings, ConfigLoader, ConfigManager, ConfigurationError
from pydantic import field_validator

BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_ENV_PATH = BACKEND_DIR / ".env"

_REQUIRED_CORS_ORIGINS: tuple[str, ...] = (
    "http://localhost:5199",
    "http://127.0.0.1:5199",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
)


class DotEnvFileLoader(ConfigLoader):
    """读取 dotenv 文件本身，不写入、不读取进程环境变量。"""

    def supports(self, path: Path) -> bool:
        name = path.name
        return name == ".env" or name.startswith(".env.") or path.suffix.lower() == ".env"

    def load(self, path: Path) -> dict[str, Any]:
        if not path.is_file():
            raise ConfigurationError(
                f"Configuration file not found: {path}",
                config_path=str(path),
            )
        raw = dotenv_values(path)
        result: dict[str, Any] = {}
        for key, value in raw.items():
            if not key or value is None:
                continue
            result[key.lower()] = value
        return result


class AppSettings(BaseSettings):
    """tech-spec §4 后端 config 键。敏感项从 backend/.env 读取，禁止硬编码密钥。"""

    database_path: str = "data/aily.db"
    upload_dir: str = "data/uploads"
    host: str = "127.0.0.1"
    port: int = 8099
    debug: bool = True
    secret_key: str
    cors_origins: list[str] = [
        "http://localhost:5199",
        "http://127.0.0.1:5199",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ]
    mock_mode: bool = True
    mock_model_name: str = "aily-mock-v1"
    mock_deterministic_seed: int = 42
    mock_user_id: str = "mock-linxiaobei"
    mock_user_display_name: str = "林小北"
    mock_user_department: str = "产品部"
    rag_top_k: int = 5
    rag_min_score: float = 0.75
    knowledge_refuse_demo_query: str = "公司上市时间表是什么？"
    meeting_default_duration_minutes: int = 60
    meeting_default_type: Literal["online", "offline"] = "online"
    meeting_disambiguation_person_name: str = "张明"
    meeting_timeout_demo_conversation_id: str = "conv-demo-meeting-timeout"
    tool_timeout_seconds: int = 30
    confirmation_execution_wait_seconds: int = 30
    meeting_room_query_after_hour: int = 15
    meeting_room_query_demo_date_offset_days: int = 1
    conversation_list_limit: int = 20
    conversation_default_title: str = "新对话"
    http_client_timeout_seconds: int = 30
    trace_event_detail_max_chars: int = 500
    weekly_report_skill_id: str = "generate_work_report"
    create_meeting_skill_id: str = "create_meeting"
    evaluation_case_count_expected: int = 7
    agent_frontend_port: int = 5199
    user_acceptance_frontend_port: int = 5175
    user_acceptance_backend_port: int = 8003

    @field_validator("debug", "mock_mode", mode="before")
    @classmethod
    def parse_bool(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        raise ValueError("CORS_ORIGINS 必须是逗号分隔字符串或列表")

    @field_validator("cors_origins")
    @classmethod
    def require_agent_and_gate_origins(cls, value: list[str]) -> list[str]:
        missing = [origin for origin in _REQUIRED_CORS_ORIGINS if origin not in value]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"CORS_ORIGINS 必须包含 Agent 与门禁四面 origin，缺少: {joined}")
        return value

    @field_validator("secret_key")
    @classmethod
    def secret_key_must_exist(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("SECRET_KEY 必须在 backend/.env 配置")
        return value


def resolve_env_path() -> Path:
    """定位 backend/.env：支持从项目根或 backend/ 目录启动。"""
    candidates = [
        DEFAULT_ENV_PATH,
        Path.cwd() / "backend" / ".env",
        Path.cwd() / ".env",
    ]
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            return resolved
    raise ConfigurationError(
        "未找到配置文件 backend/.env",
        config_path=str(DEFAULT_ENV_PATH),
    )


def _prepare_manager() -> ConfigManager[AppSettings]:
    manager: ConfigManager[AppSettings] = ConfigManager()
    loaders: list[ConfigLoader] = manager._loaders
    if not any(isinstance(item, DotEnvFileLoader) for item in loaders):
        manager.register_loader(DotEnvFileLoader())
    return manager


def load_settings(env_path: Path | None = None) -> AppSettings:
    """从 .env 加载配置；use_env=False，禁止进程环境覆盖。"""
    path = env_path if env_path is not None else resolve_env_path()
    manager = _prepare_manager()
    manager.load(AppSettings, path, use_env=False)
    return cast(AppSettings, manager.settings)


config: ConfigManager[AppSettings] = ConfigManager()
settings = load_settings()
