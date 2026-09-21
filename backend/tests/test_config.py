from pathlib import Path

from src.core.config import AppSettings, settings

TECH_SPEC_BACKEND_CONFIG_KEYS = (
    "database_path",
    "upload_dir",
    "host",
    "port",
    "debug",
    "secret_key",
    "cors_origins",
    "mock_mode",
    "mock_model_name",
    "mock_deterministic_seed",
    "mock_user_id",
    "mock_user_display_name",
    "mock_user_department",
    "rag_top_k",
    "rag_min_score",
    "knowledge_refuse_demo_query",
    "meeting_default_duration_minutes",
    "meeting_default_type",
    "meeting_disambiguation_person_name",
    "meeting_timeout_demo_conversation_id",
    "tool_timeout_seconds",
    "confirmation_execution_wait_seconds",
    "meeting_room_query_after_hour",
    "meeting_room_query_demo_date_offset_days",
    "conversation_list_limit",
    "http_client_timeout_seconds",
    "trace_event_detail_max_chars",
    "weekly_report_skill_id",
    "create_meeting_skill_id",
    "evaluation_case_count_expected",
    "agent_frontend_port",
    "user_acceptance_frontend_port",
    "user_acceptance_backend_port",
)

ENV_EXAMPLE_PATH = Path(__file__).resolve().parents[1] / ".env.example"


def _example_keys() -> set[str]:
    keys: set[str] = set()
    for line in ENV_EXAMPLE_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        keys.add(stripped.split("=", 1)[0].strip().lower())
    return keys


def test_settings_exposes_all_tech_spec_backend_keys() -> None:
    for key in TECH_SPEC_BACKEND_CONFIG_KEYS:
        assert hasattr(settings, key)


def test_env_example_keys_match_settings_fields() -> None:
    example_keys = _example_keys()
    field_keys = set(AppSettings.model_fields)
    assert example_keys == field_keys


def test_secret_key_comes_from_env_and_is_non_empty() -> None:
    assert settings.secret_key.strip()


def test_cors_origins_include_agent_and_gate_ports() -> None:
    origins = set(settings.cors_origins)
    assert "http://localhost:5199" in origins
    assert "http://127.0.0.1:5199" in origins
    assert "http://localhost:5175" in origins
    assert "http://127.0.0.1:5175" in origins


def test_storage_paths_match_env_policy() -> None:
    assert settings.database_path == "data/aily.db"
    assert settings.upload_dir == "data/uploads"


def test_agent_backend_port_is_8099() -> None:
    assert settings.port == 8099


def test_mock_identity_config() -> None:
    assert settings.mock_user_id == "mock-linxiaobei"
    assert settings.mock_user_display_name == "林小北"
    assert settings.mock_user_department == "产品部"


def test_env_example_contains_required_key_names_without_secrets() -> None:
    text = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    assert "SECRET_KEY=" in text
    assert "sk-" not in text
    assert "Bearer " not in text
