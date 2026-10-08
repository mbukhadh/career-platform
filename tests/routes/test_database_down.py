from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def test_a_page_still_loads_when_the_database_is_down(tmp_path, monkeypatch):
    unreachable = tmp_path / "missing-folder" / "career.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{unreachable}")
    monkeypatch.setenv("SNAPSHOT_DIR", str(tmp_path / "snapshots"))
    get_settings.cache_clear()
    try:
        client = TestClient(create_app())
        page = client.get("/")
        health = client.get("/healthz")
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()

    assert page.status_code == 503
    assert "text/html" in page.headers["content-type"]
    assert "static/css/site.css" in page.text
    assert health.status_code == 200
