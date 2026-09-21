"""AC-F006-04 案例覆盖主链且两次列表一致。"""

from fastapi.testclient import TestClient
from tests.features.f006.conftest import EXPECTED_CASE_IDS, assert_envelope_ok


def test_list_is_stable_across_two_reads(client: TestClient) -> None:
    first = assert_envelope_ok(client.get("/api/evaluation_cases").json())
    second = assert_envelope_ok(client.get("/api/evaluation_cases").json())
    assert first == second
    names = {item["name"] for item in first["items"]}
    assert names == {
        "差旅住宿标准",
        "无依据问句拒答",
        "创建项目复盘会",
        "创建会议超时",
        "改时间后重确认",
        "生成本周周报",
        "查询可用会议室",
    }
    assert [item["case_id"] for item in first["items"]] == EXPECTED_CASE_IDS
    categories = {item["bad_case_category"] for item in first["items"]}
    assert "timeout_unknown" in categories
    assert "confirmation_invalidated" in categories
    assert "no_evidence_refusal" in categories
