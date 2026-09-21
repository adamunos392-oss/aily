"""AC-F006-02 打开案例可见事件流回放。"""

from fastapi.testclient import TestClient
from tests.features.f006.conftest import assert_envelope_ok


def test_timeout_case_replay(client: TestClient) -> None:
    response = client.get("/api/evaluation_cases/eval-meeting-timeout")
    assert response.status_code == 200
    data = assert_envelope_ok(response.json())
    assert data["replay_note"] == "只读回放，不创建会议、不写入企业知识"
    case = data["case"]
    assert case["case_id"] == "eval-meeting-timeout"
    titles = [item["title_zh"] for item in case["trace_events"]]
    assert titles == ["确认已同意", "原子能力超时", "结果核验未知", "最终未知 · 无会议已创建"]
    assert all(item["sequence"] == index for index, item in enumerate(case["trace_events"], start=1))
    comparison = data["route_comparison"]
    assert comparison["expected_route"] == case["expected_route"]
    assert comparison["actual_route"] == case["actual_route"]
    assert comparison["passed"] is True


def test_travel_case_replay_omits_unhappened_steps(client: TestClient) -> None:
    data = assert_envelope_ok(client.get("/api/evaluation_cases/eval-qa-travel").json())
    titles = [item["title_zh"] for item in data["case"]["trace_events"]]
    assert titles == [
        "问题改写",
        "意图识别",
        "路由到企业知识",
        "知识检索",
        "引用核验通过",
        "最终已回复",
    ]
    assert "原子能力超时" not in titles
    assert "确认已同意" not in titles


def test_missing_case_is_not_found(client: TestClient) -> None:
    response = client.get("/api/evaluation_cases/eval-missing")
    assert response.status_code == 404
    body = response.json()
    assert body["code"] == 404
    assert body["message"] == "评测案例不存在"
    assert body["data"] is None
