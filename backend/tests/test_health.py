from pathlib import Path

from fastapi.testclient import TestClient

from src.main import app, server


def test_health_returns_200() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"


def test_app_is_created_by_apiserver_not_raw_fastapi() -> None:
    assert server.app is app
    source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
    assert "APIServer" in source
    assert "FastAPI(" not in source
