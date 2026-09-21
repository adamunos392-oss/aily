"""SQLite 路径解析与异步会话。基于 pycore/integrations/db/session.py 模板扩展。"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from pycore.core import get_logger
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import BACKEND_DIR, settings
from src.db.models import Base
from src.db.seed import seed_database


def resolve_database_file(database_path: str, *, base_dir: Path | None = None) -> Path:
    """将 DATABASE_PATH 解析为绝对路径，相对路径相对 backend/，并创建父目录。"""
    root = base_dir if base_dir is not None else BACKEND_DIR
    path = Path(database_path)
    if not path.is_absolute():
        path = root / path
    resolved = path.resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def resolve_upload_dir(upload_dir: str, *, base_dir: Path | None = None) -> Path:
    """将 UPLOAD_DIR 解析为绝对路径并创建目录。"""
    root = base_dir if base_dir is not None else BACKEND_DIR
    path = Path(upload_dir)
    if not path.is_absolute():
        path = root / path
    resolved = path.resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def sqlite_url_for(db_file: Path) -> str:
    return f"sqlite+aiosqlite:///{db_file.resolve().as_posix()}"


def _enable_sqlite_foreign_keys(dbapi_connection: Any, _connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


def create_engine(database_url: str) -> AsyncEngine:
    engine = create_async_engine(database_url, echo=False, future=True)
    event.listen(engine.sync_engine, "connect", _enable_sqlite_foreign_keys)
    return engine


DATABASE_FILE = resolve_database_file(settings.database_path)
DATABASE_URL = sqlite_url_for(DATABASE_FILE)
UPLOAD_DIR = resolve_upload_dir(settings.upload_dir)

engine = create_engine(DATABASE_URL)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（用于 FastAPI Depends）。成功提交，异常回滚。"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """上下文管理器形式的数据库会话。"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_all_tables(bind: AsyncEngine | None = None) -> None:
    """对指定引擎执行 create_all；默认使用运行时 engine。"""
    target = bind if bind is not None else engine
    async with target.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def init_db() -> None:
    """初始化数据库：create_all + 幂等 seed。"""
    resolve_upload_dir(settings.upload_dir)
    resolve_database_file(settings.database_path)
    await create_all_tables(engine)
    async with async_session_maker() as session:
        await seed_database(session)
        await session.commit()
    get_logger().info("数据库已初始化", db_path=str(DATABASE_FILE))


async def close_db() -> None:
    """关闭数据库连接。"""
    await engine.dispose()
    get_logger().info("数据库连接已关闭")
