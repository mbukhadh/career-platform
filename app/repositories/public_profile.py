from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.public_profile import (
    PublicAccomplishment,
    PublicEducation,
    PublicExperience,
    PublicProject,
    PublicSkill,
    PublicSkillGroup,
    PublishedProfile,
    serialize_public_profile,
)
from app.models import Profile

__all__ = ["get_published_profile", "serialize_public_profile"]


def get_published_profile(session: Session, slug: str) -> PublishedProfile | None:
    profile = session.scalar(
        select(Profile).where(Profile.slug == slug, Profile.is_published.is_(True))
    )
    if profile is None:
        return None

    experiences = tuple(
        PublicExperience(
            employer=item.employer,
            title=item.title,
            start_date=item.start_date,
            end_date=item.end_date,
            location=item.location,
            summary=item.summary,
            display_order=item.display_order,
            is_published=item.is_published,
            accomplishments=tuple(
                PublicAccomplishment(
                    content=accomplishment.content,
                    display_order=accomplishment.display_order,
                )
                for accomplishment in sorted(
                    item.accomplishments, key=lambda value: value.display_order
                )
            ),
        )
        for item in sorted(
            (item for item in profile.experiences if item.is_published),
            key=lambda value: value.display_order,
        )
    )
    education = tuple(
        PublicEducation(
            institution=item.institution,
            program=item.program,
            start_date=item.start_date,
            end_date=item.end_date,
            details=item.details,
            display_order=item.display_order,
        )
        for item in sorted(
            (item for item in profile.education if item.is_published),
            key=lambda value: value.display_order,
        )
    )
    skill_groups = tuple(
        PublicSkillGroup(
            name=group.name,
            display_order=group.display_order,
            skills=tuple(
                PublicSkill(name=skill.name, display_order=skill.display_order)
                for skill in sorted(
                    (skill for skill in group.skills if skill.is_published),
                    key=lambda value: value.display_order,
                )
            ),
        )
        for group in sorted(
            (group for group in profile.skill_groups if group.is_published),
            key=lambda value: value.display_order,
        )
    )
    projects = tuple(
        PublicProject(
            name=item.name,
            description=item.description,
            url=item.url,
            display_order=item.display_order,
        )
        for item in sorted(
            (item for item in profile.projects if item.is_published),
            key=lambda value: value.display_order,
        )
    )
    return PublishedProfile(
        slug=profile.slug,
        name=profile.name,
        headline=profile.headline,
        summary=profile.summary,
        location=profile.location,
        github_url=profile.github_url,
        linkedin_url=profile.linkedin_url,
        experiences=experiences,
        education=education,
        skill_groups=skill_groups,
        projects=projects,
    )
