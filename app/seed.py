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
from app.profile_content import PROFILE


def seed_database(session: Session) -> None:
    profile = session.scalar(select(Profile).where(Profile.slug == PROFILE.slug))
    if profile is not None:
        return

    owner = Owner(name=PROFILE.name)
    profile = Profile(
        owner=owner,
        slug=PROFILE.slug,
        name=PROFILE.name,
        headline=PROFILE.headline,
        summary=PROFILE.summary,
        location=PROFILE.location,
        github_url=PROFILE.github_url,
        linkedin_url=PROFILE.linkedin_url,
        is_published=True,
    )
    profile.experiences = [
        Experience(
            employer=item.employer,
            title=item.title,
            start_date=item.start_date,
            end_date=item.end_date,
            location=item.location,
            summary=item.summary,
            display_order=item.display_order,
            is_published=True,
        )
        for item in PROFILE.experiences
    ]
    profile.education = [
        Education(
            institution=item.institution,
            program=item.program,
            start_date=item.start_date,
            end_date=item.end_date,
            details=item.details,
            display_order=item.display_order,
            is_published=True,
        )
        for item in PROFILE.education
    ]
    profile.skill_groups = [
        SkillGroup(
            name=group.name,
            display_order=group.display_order,
            is_published=True,
            skills=[
                Skill(
                    name=skill.name,
                    display_order=skill.display_order,
                    is_published=True,
                )
                for skill in group.skills
            ],
        )
        for group in PROFILE.skill_groups
    ]
    profile.projects = [
        Project(
            name="Career Platform",
            description=(
                "A database-driven resume site built with FastAPI and SQLite "
                "in GitHub Codespaces."
            ),
            url="https://github.com/mbukhadh/career-platform",
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
