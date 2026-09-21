"""AC-F001-04 / API-F001-01 演示身份。"""

from fastapi.testclient import TestClient
from tests.features.f001.conftest import assert_envelope_ok

from src.core.config import settings


def test_identity_returns_linxiaobei(client: TestClient) -> None:
    response = client.get("/api/identity")
    assert response.status_code == 200
    data = assert_envelope_ok(response.json())
    assert data["user_id"] == settings.mock_user_id
    assert data["display_name"] == "林小北"
    assert data["department"] == "产品部"
    assert data["permissions"] == [
        "conversation:read",
        "conversation:write",
        "knowledge:read",
    ]
