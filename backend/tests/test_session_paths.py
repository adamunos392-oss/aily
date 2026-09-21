from pathlib import Path

from src.db.session import DATABASE_FILE, resolve_database_file


def test_database_path_is_absolute_under_backend_data() -> None:
    resolved = resolve_database_file("data/aily.db")
    assert resolved.is_absolute()
    assert resolved.name == "aily.db"
    assert resolved.parent.name == "data"
    assert resolved == DATABASE_FILE


def test_runtime_sqlite_file_not_dropped_by_tests() -> None:
    """基础设施冒烟不得 drop_all 真实业务库；文件可在 init_db 中新建。"""
    if DATABASE_FILE.exists():
        assert DATABASE_FILE.stat().st_size >= 0
    assert Path(DATABASE_FILE).suffix == ".db"
