from dataclasses import asdict, dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class PublicAccomplishment:
    content: str
    display_order: int


@dataclass(frozen=True)
class PublicExperience:
    employer: str
    title: str
    start_date: date | None
    end_date: date | None
    location: str | None
    summary: str
    display_order: int
    is_published: bool = True
    accomplishments: tuple[PublicAccomplishment, ...] = ()


@dataclass(frozen=True)
class PublicEducation:
    institution: str
    program: str
    start_date: date | None
    end_date: date | None
    details: str | None
    display_order: int


@dataclass(frozen=True)
class PublicSkill:
    name: str
    display_order: int


@dataclass(frozen=True)
class PublicSkillGroup:
    name: str
    display_order: int
    skills: tuple[PublicSkill, ...] = ()


@dataclass(frozen=True)
class PublicProject:
    name: str
    description: str
    url: str | None
    display_order: int


@dataclass(frozen=True)
class PublishedProfile:
    slug: str
    name: str
    headline: str
    summary: str
    location: str | None
    github_url: str | None = None
    linkedin_url: str | None = None
    experiences: tuple[PublicExperience, ...] = ()
    education: tuple[PublicEducation, ...] = ()
    skill_groups: tuple[PublicSkillGroup, ...] = ()
    projects: tuple[PublicProject, ...] = ()


def serialize_public_profile(profile: PublishedProfile) -> dict[str, Any]:
    return asdict(profile)
