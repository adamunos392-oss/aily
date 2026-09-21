"""路由汇出。main.py 只从本包 include_router。"""

from src.api.routes.confirmations import router as confirmations_router
from src.api.routes.conversations import router as conversations_router
from src.api.routes.evaluation_cases import router as evaluation_cases_router
from src.api.routes.identity import router as identity_router

__all__ = [
    "confirmations_router",
    "conversations_router",
    "evaluation_cases_router",
    "identity_router",
]
