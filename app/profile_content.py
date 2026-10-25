"""The public profile, kept in code so it renders even when the database is down.

Only projects are read from the database on each request. `app/seed.py`
builds the profile rows for local databases from this same object.
"""

from datetime import date

from app.domain.public_profile import (
    PublicEducation,
    PublicExperience,
    PublicSkill,
    PublicSkillGroup,
    PublishedProfile,
)

PROFILE = PublishedProfile(
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
    experiences=(
        PublicExperience(
            employer="",
            title="Experience — coming soon",
            start_date=None,
            end_date=None,
            location=None,
            summary="",
            display_order=0,
        ),
    ),
    education=(
        PublicEducation(
            institution="Loyola Marymount University",
            program="B.S. Information Systems & Business Analytics",
            start_date=None,
            end_date=date(2027, 5, 31),
            details=None,
            display_order=0,
        ),
    ),
    skill_groups=(
        PublicSkillGroup(
            name="Programming & Data",
            display_order=0,
            skills=(
                PublicSkill(name="Python", display_order=0),
                PublicSkill(name="SQL", display_order=1),
            ),
        ),
    ),
)
