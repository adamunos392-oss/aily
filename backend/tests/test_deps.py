from fastapi.testclient import TestClient
from starlette.middleware.cors import CORSMiddleware

from src.api.deps import get_current_user
from src.main import app


def test_cors_middleware_registered() -> None:
    middleware_classes = [item.cls for item in app.user_middleware]
    assert CORSMiddleware in middleware_classes


def test_health_allows_agent_origin() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:5199"},
        )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5199"


def test_health_allows_acceptance_origin() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:5175"},
        )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5175"


async def test_get_current_user_returns_mock_linxiaobei() -> None:
    user = await get_current_user()
    assert user.user_id == "mock-linxiaobei"
    assert user.display_name == "林小北"
    assert user.department == "产品部"
    assert user.permissions == [
        "conversation:read",
        "conversation:write",
        "knowledge:read",
    ]
