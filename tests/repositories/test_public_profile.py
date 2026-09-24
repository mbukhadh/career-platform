from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, Experience, Profile
from app.repositories.public_profile import (
    get_published_profile,
    serialize_public_profile,
)
from app.seed import seed_database


def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_repository_excludes_unpublished_children():
    with session() as db:
        seed_database(db)
        profile = db.query(Profile).filter_by(slug="mj-bukhadhour").one()
        profile.experiences.append(
            Experience(
                employer="Secret",
                title="Hidden",
                start_date=date(2020, 1, 1),
                summary="Not public",
                display_order=99,
                is_published=False,
            )
        )
        db.commit()

        result = get_published_profile(db, profile.slug)

        assert result is not None
        assert all(item.is_published for item in result.experiences)


def test_serialized_profile_contains_no_contact_destination():
    with session() as db:
        seed_database(db)
        result = get_published_profile(db, "mj-bukhadhour")
        payload = serialize_public_profile(result)
        assert "to_address" not in repr(payload)
