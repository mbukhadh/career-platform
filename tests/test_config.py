import pytest

from app.config import Settings, normalize_database_url


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("postgres://u:p@db.example:5432/app", "postgresql+psycopg://u:p@db.example:5432/app"),
        ("postgresql://u:p@db.example:5432/app", "postgresql+psycopg://u:p@db.example:5432/app"),
        ("postgresql+psycopg://u:p@db.example/app", "postgresql+psycopg://u:p@db.example/app"),
        ("sqlite:///./career_platform.db", "sqlite:///./career_platform.db"),
    ],
)
def test_database_url_uses_the_installed_postgres_driver(given, expected):
    assert normalize_database_url(given) == expected


def test_settings_normalize_the_url_from_the_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@db.example:5432/app")
    assert Settings().database_url == "postgresql+psycopg://u:p@db.example:5432/app"


def test_local_default_stays_on_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert Settings(_env_file=None).database_url == "sqlite:///./career_platform.db"
