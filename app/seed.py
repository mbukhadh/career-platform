from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_engine
from app.models import (
    Base,
    ContactConfiguration,
    Education,
    Experience,
    ExperienceAccomplishment,
    Owner,
    Profile,
    Project,
    Skill,
    SkillGroup,
)


def seed_database(session: Session) -> None:
    profile = session.scalar(select(Profile).where(Profile.slug == "jane-doe"))
    if profile is not None:
        return

    owner = Owner(name="Jane Doe")
    profile = Profile(
        owner=owner,
        slug="jane-doe",
        name="Jane Doe",
        headline="Software engineer building useful products",
        summary="Software engineer focused on reliable, human-centered web products.",
        location="Codespaces",
        is_published=True,
    )
    experience = Experience(
        profile=profile,
        employer="Example Labs",
        title="Senior Software Engineer",
        start_date=date(2022, 1, 1),
        summary="Builds and operates product experiences for growing teams.",
        display_order=0,
        is_published=True,
        accomplishments=[
            ExperienceAccomplishment(
                content="Improved product reliability through focused platform work.",
                display_order=0,
            )
        ],
    )
    previous = Experience(
        profile=profile,
        employer="Earlier Company",
        title="Software Engineer",
        start_date=date(2019, 1, 1),
        end_date=date(2021, 12, 31),
        summary="Delivered customer-facing web applications.",
        display_order=1,
        is_published=True,
    )
    profile.experiences = [experience, previous]
    profile.education = [
        Education(
            institution="Example University",
            program="Computer Science",
            start_date=date(2015, 9, 1),
            end_date=date(2019, 5, 31),
            display_order=0,
            is_published=True,
        )
    ]
    tools = SkillGroup(name="Tools", display_order=0, is_published=True)
    tools.skills = [
        Skill(name="Python", display_order=0, is_published=True),
        Skill(name="SQL", display_order=1, is_published=True),
    ]
    profile.skill_groups = [tools]
    profile.projects = [
        Project(
            name="Career Platform",
            description="A structured foundation for a resilient career profile.",
            url="https://example.com/career-platform",
            display_order=0,
            is_published=True,
        )
    ]
    settings = get_settings()
    profile.contact_configuration = ContactConfiguration(
        to_address=settings.contact_to or "owner@example.com",
        from_address=settings.contact_from,
    )
    session.add(profile)
    session.flush()


def main() -> None:
    settings = get_settings()
    engine = get_engine(settings)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)
        session.commit()


if __name__ == "__main__":
    main()
