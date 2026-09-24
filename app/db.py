from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings


def get_engine(settings: Settings):
    return create_engine(settings.database_url, future=True)


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
