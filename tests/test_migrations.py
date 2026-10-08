from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.config import get_settings


def test_migrations_run_against_the_configured_database(tmp_path, monkeypatch):
    local_default = Path("career_platform.db")
    before = local_default.stat().st_mtime_ns if local_default.exists() else None
    database_path = tmp_path / "migrated.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    get_settings.cache_clear()
    try:
        command.upgrade(Config("alembic.ini"), "head")
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()

    engine = create_engine(f"sqlite:///{database_path}")
    assert "profiles" in inspect(engine).get_table_names()
    with engine.connect() as connection:
        version = connection.scalar(text("select version_num from alembic_version"))
    assert version == "0001_initial_schema"
    after = local_default.stat().st_mtime_ns if local_default.exists() else None
    assert after == before
