from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, Profile
from app.seed import seed_database


def test_seed_creates_one_published_profile_with_ordered_content():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)
        profile = session.query(Profile).filter_by(slug="mj-bukhadhour").one()
        assert profile.is_published is True
        assert profile.skill_groups[0].name == "Programming & Data"
        assert profile.experiences[0].title == "Experience — coming soon"
        assert profile.experiences[0].employer == ""
        assert profile.experiences[0].start_date is None
        assert profile.education[0].end_date.year == 2027
        assert [item.display_order for item in profile.projects] == sorted(
            item.display_order for item in profile.projects
        )


def test_contact_destination_is_not_public_profile_data():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)
        profile = session.query(Profile).filter_by(slug="mj-bukhadhour").one()
        assert hasattr(profile, "contact_configuration")
        assert profile.contact_configuration.to_address
