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
    Owner,
    Profile,
    Project,
    Skill,
    SkillGroup,
)


def seed_database(session: Session) -> None:
    profile = session.scalar(select(Profile).where(Profile.slug == "mj-bukhadhour"))
    if profile is not None:
        return

    owner = Owner(name="Mohammad (MJ) Bukhadhour")
    profile = Profile(
        owner=owner,
        slug="mj-bukhadhour",
        name="Mohammad (MJ) Bukhadhour",
        headline="Information Systems & Business Analytics student at LMU",
        summary=(
            "Senior at Loyola Marymount University studying Information Systems "
            "and Business Analytics, graduating May 2027."
        ),
        location="Los Angeles, California",
        github_url="https://github.com/mbukhadh",
        linkedin_url="https://www.linkedin.com/in/mohammad-bukhadhour-ab7235391/",
        is_published=True,
    )
    experience = Experience(
        profile=profile,
        employer="",
        title="Experience — coming soon",
        start_date=None,
        summary="",
        display_order=0,
        is_published=True,
    )
    profile.experiences = [experience]
    profile.education = [
        Education(
            institution="Loyola Marymount University",
            program="B.S. Information Systems & Business Analytics",
            end_date=date(2027, 5, 31),
            display_order=0,
            is_published=True,
        )
    ]
    tools = SkillGroup(name="Programming & Data", display_order=0, is_published=True)
    tools.skills = [
        Skill(name="Python", display_order=0, is_published=True),
        Skill(name="SQL", display_order=1, is_published=True),
    ]
    profile.skill_groups = [tools]
    profile.projects = [
        Project(
            name="Career Platform",
            description=(
                "A database-driven resume site built with FastAPI and SQLite "
                "in GitHub Codespaces."
            ),
            url="https://github.com/mbukhadh/career_platform",
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
