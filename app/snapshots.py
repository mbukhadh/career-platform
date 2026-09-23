import json
import logging
import os
import tempfile
from collections.abc import Callable
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy.exc import DBAPIError, OperationalError

from app.domain.public_profile import (
    PublicAccomplishment,
    PublicEducation,
    PublicExperience,
    PublicProject,
    PublicSkill,
    PublicSkillGroup,
    PublishedProfile,
)

logger = logging.getLogger(__name__)


def _json_default(value: object) -> str:
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"Unsupported snapshot value: {type(value).__name__}")


def _profile_from_payload(payload: object, slug: str) -> PublishedProfile:
    if not isinstance(payload, dict) or payload.get("slug") != slug:
        raise ValueError("snapshot profile mismatch")
    profile_payload: dict[str, Any] = payload
    required = ("name", "headline", "summary", "location")
    if any(key not in profile_payload for key in required):
        raise ValueError("snapshot missing profile field")

    def items(name: str) -> list[dict[str, Any]]:
        values = profile_payload.get(name, [])
        if not isinstance(values, list):
            raise TypeError(f"snapshot field {name} must be a list")
        if not all(isinstance(item, dict) for item in values):
            raise TypeError(f"snapshot field {name} contains an invalid item")
        return values

    experiences = tuple(
        PublicExperience(
            employer=item["employer"],
            title=item["title"],
            start_date=date.fromisoformat(item["start_date"]),
            end_date=date.fromisoformat(item["end_date"])
            if item.get("end_date")
            else None,
            location=item.get("location"),
            summary=item["summary"],
            display_order=item["display_order"],
            accomplishments=tuple(
                PublicAccomplishment(
                    content=accomplishment["content"],
                    display_order=accomplishment["display_order"],
                )
                for accomplishment in item.get("accomplishments", [])
            ),
        )
        for item in items("experiences")
    )
    education = tuple(
        PublicEducation(
            institution=item["institution"],
            program=item["program"],
            start_date=date.fromisoformat(item["start_date"])
            if item.get("start_date")
            else None,
            end_date=date.fromisoformat(item["end_date"])
            if item.get("end_date")
            else None,
            details=item.get("details"),
            display_order=item["display_order"],
        )
        for item in items("education")
    )
    groups = tuple(
        PublicSkillGroup(
            name=item["name"],
            display_order=item["display_order"],
            skills=tuple(
                PublicSkill(name=skill["name"], display_order=skill["display_order"])
                for skill in item.get("skills", [])
            ),
        )
        for item in items("skill_groups")
    )
    projects = tuple(
        PublicProject(
            name=item["name"],
            description=item["description"],
            url=item.get("url"),
            display_order=item["display_order"],
        )
        for item in items("projects")
    )
    return PublishedProfile(
        slug=slug,
        name=profile_payload["name"],
        headline=profile_payload["headline"],
        summary=profile_payload["summary"],
        location=profile_payload["location"],
        experiences=experiences,
        education=education,
        skill_groups=groups,
        projects=projects,
    )


def write_snapshot(snapshot_dir: Path, profile: PublishedProfile) -> Path:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(asdict(profile), default=_json_default, sort_keys=True)
    _profile_from_payload(json.loads(payload), profile.slug)
    destination = snapshot_dir / f"{profile.slug}-v{uuid4().hex}.json"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=snapshot_dir, delete=False
    ) as temporary:
        temporary.write(payload)
        temporary.flush()
        os.fsync(temporary.fileno())
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, destination)
    return destination


def read_latest_snapshot(snapshot_dir: Path, slug: str) -> PublishedProfile | None:
    candidates = sorted(
        snapshot_dir.glob(f"{slug}-v*.json"),
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )
    for candidate in candidates:
        try:
            with candidate.open(encoding="utf-8") as snapshot_file:
                return _profile_from_payload(json.load(snapshot_file), slug)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            logger.warning(
                "Ignoring invalid public profile snapshot", extra={"slug": slug}
            )
    return None


def load_profile_with_fallback(
    slug: str,
    db_loader: Callable[[], PublishedProfile | None],
    snapshot_dir: Path,
) -> tuple[PublishedProfile | None, str]:
    try:
        profile = db_loader()
    except (ConnectionError, OperationalError, DBAPIError):
        logger.exception("Public profile database unavailable")
        profile = None
    else:
        if profile is not None:
            return profile, "database"
        return None, "database"

    profile = read_latest_snapshot(snapshot_dir, slug)
    return profile, "snapshot"
