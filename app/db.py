from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import Settings


@lru_cache
def _engine_for(database_url: str) -> Engine:
    if database_url.startswith("postgresql"):
        return create_engine(
            database_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 5},
        )
    if database_url.startswith("sqlite") and ":memory:" not in database_url:
        # No pool for file databases: each request opens the file again, so a
        # missing or replaced file shows up on the next request instead of
        # being hidden by a connection that still holds the old file open.
        return create_engine(database_url, poolclass=NullPool)
    return create_engine(database_url, future=True)


def get_engine(settings: Settings) -> Engine:
    return _engine_for(settings.database_url)


def get_session_factory(settings: Settings) -> sessionmaker[Session]:
    return sessionmaker(get_engine(settings), expire_on_commit=False)


def session_scope(settings: Settings) -> Generator[Session, None, None]:
    session = get_session_factory(settings)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
