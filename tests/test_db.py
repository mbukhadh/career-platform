from app.config import Settings
from app.db import get_engine


def test_one_engine_is_reused_for_the_same_database(tmp_path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'career.db'}")
    assert get_engine(settings) is get_engine(settings)


def test_postgres_engine_checks_connections_and_times_out():
    settings = Settings(database_url="postgresql://u:p@db.example:5432/app")
    engine = get_engine(settings)
    assert engine.dialect.name == "postgresql"
    assert engine.dialect.driver == "psycopg"
    assert engine.pool._pre_ping is True
