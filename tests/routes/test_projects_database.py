"""Projects come from the database on every request; the profile never does."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import get_settings
from app.main import create_app
from app.models import Base
from app.seed import seed_database

PROFILE_NAME = "Mohammad (MJ) Bukhadhour"
UNAVAILABLE = "Projects temporarily unavailable"


def _build_database(path, *, seed: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(engine)
    if seed:
        with Session(engine) as session:
            seed_database(session)
            session.commit()
    engine.dispose()


def _client(monkeypatch, db_path) -> TestClient:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()
    return TestClient(create_app())


def teardown_function():
    get_settings.cache_clear()


def test_healthy_database_shows_projects_with_200(tmp_path, monkeypatch):
    db_path = tmp_path / "career.db"
    _build_database(db_path, seed=True)

    response = _client(monkeypatch, db_path).get("/")

    assert response.status_code == 200
    assert PROFILE_NAME in response.text
    assert "<h3>Career Platform</h3>" in response.text
    assert UNAVAILABLE not in response.text
    assert "Projects source: database" in response.text


def test_empty_projects_table_returns_200_with_empty_message(tmp_path, monkeypatch):
    db_path = tmp_path / "career.db"
    _build_database(db_path, seed=False)

    response = _client(monkeypatch, db_path).get("/")

    assert response.status_code == 200
    assert PROFILE_NAME in response.text
    assert "No projects published yet." in response.text
    assert UNAVAILABLE not in response.text


def test_database_failure_keeps_profile_and_returns_503(tmp_path, monkeypatch):
    db_path = tmp_path / "missing-folder" / "career.db"

    client = _client(monkeypatch, db_path)
    response = client.get("/")

    assert response.status_code == 503
    assert PROFILE_NAME in response.text
    assert "Loyola Marymount University" in response.text
    assert UNAVAILABLE in response.text
    assert "Career Platform</h3>" not in response.text
    assert "No projects published" not in response.text
    assert "static/css/site.css" in response.text
    assert client.get("/healthz").status_code == 200


def test_next_request_recovers_without_restart(tmp_path, monkeypatch):
    db_path = tmp_path / "missing-folder" / "career.db"
    client = _client(monkeypatch, db_path)

    first = client.get("/")
    _build_database(db_path, seed=True)
    second = client.get("/")

    assert first.status_code == 503
    assert UNAVAILABLE in first.text
    assert second.status_code == 200
    assert "<h3>Career Platform</h3>" in second.text
    assert UNAVAILABLE not in second.text


def test_database_removed_after_healthy_request_is_reported(tmp_path, monkeypatch):
    db_path = tmp_path / "data" / "career.db"
    _build_database(db_path, seed=True)
    client = _client(monkeypatch, db_path)

    healthy = client.get("/")
    (tmp_path / "data").rename(tmp_path / "data-away")
    gone = client.get("/")

    assert healthy.status_code == 200
    assert gone.status_code == 503
    assert UNAVAILABLE in gone.text
    assert PROFILE_NAME in gone.text
