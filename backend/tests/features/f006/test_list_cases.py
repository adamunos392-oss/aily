"""AC-F006-01 验证台列出路由对照。"""

from fastapi.testclient import TestClient
from tests.features.f006.conftest import EXPECTED_CASE_IDS, assert_envelope_ok


def test_list_evaluation_cases(client: TestClient) -> None:
    response = client.get("/api/evaluation_cases")
    assert response.status_code == 200
    data = assert_envelope_ok(response.json())
    assert data["total"] == 7
    items = data["items"]
    assert [item["case_id"] for item in items] == EXPECTED_CASE_IDS
    by_id = {item["case_id"]: item for item in items}
    assert by_id["eval-meeting-timeout"]["bad_case_category"] == "timeout_unknown"
    assert by_id["eval-meeting-stale"]["bad_case_category"] == "confirmation_invalidated"
    assert by_id["eval-qa-refuse"]["bad_case_category"] == "no_evidence_refusal"
    assert by_id["eval-meeting-timeout"]["expected_route"] == "技能 create_meeting → 未知"
    assert by_id["eval-meeting-stale"]["expected_route"] == "确认作废后重确认"
    assert all(item["passed"] is True for item in items)
    for item in items:
        assert set(item.keys()) == {
            "case_id",
            "name",
            "expected_route",
            "actual_route",
            "passed",
            "bad_case_category",
        }
