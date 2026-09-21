"""
FastAPI 依赖注入。基于 pycore/api/deps.py 模板扩展。

认证为路由级 Depends，不注册全局认证中间件。
MVP 无登录 / JWT：get_current_user 返回固定 Mock UserContext（林小北｜产品部）。
运行时会话从 src.db.session.get_db 注入，不使用 pycore.integrations.db.session。
"""

from src.core.config import settings
from src.db.session import get_db
from src.models.user_context import MOCK_USER_PERMISSIONS, UserContext


async def get_current_user() -> UserContext:
    """注入固定 Mock UserContext。不读取 JWT，不查询数据库。"""
    return UserContext(
        user_id=settings.mock_user_id,
        display_name=settings.mock_user_display_name,
        department=settings.mock_user_department,
        permissions=list(MOCK_USER_PERMISSIONS),
    )


__all__ = ["get_current_user", "get_db"]
