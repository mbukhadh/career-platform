from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, Profile
from app.seed import seed_database


def test_seed_creates_one_published_profile_with_ordered_content():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)
        profile = session.query(Profile).filter_by(slug="jane-doe").one()
        assert profile.is_published is True
        assert [item.display_order for item in profile.projects] == sorted(
            item.display_order for item in profile.projects
        )


def test_contact_destination_is_not_public_profile_data():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)
        profile = session.query(Profile).filter_by(slug="jane-doe").one()
        assert hasattr(profile, "contact_configuration")
        assert profile.contact_configuration.to_address
