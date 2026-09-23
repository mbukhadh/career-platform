from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Base
from app.seed import seed_database
from app.generate_snapshot import run_snapshot_command


def test_snapshot_command_writes_public_snapshot(tmp_path, monkeypatch):
    database_path = tmp_path / "career.db"
    engine = create_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)
        session.commit()

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("SNAPSHOT_DIR", str(tmp_path / "snapshots"))
    get_settings.cache_clear()

    run_snapshot_command(["--slug", "jane-doe"])

    files = list((tmp_path / "snapshots").glob("*.json"))
    assert files
    assert "to_address" not in files[0].read_text()
