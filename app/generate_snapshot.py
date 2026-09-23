import argparse
from pathlib import Path

from app.config import get_settings
from app.db import get_session_factory
from app.repositories.public_profile import get_published_profile
from app.snapshots import write_snapshot


def run_snapshot_command(arguments: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True)
    args = parser.parse_args(arguments)
    settings = get_settings()
    with get_session_factory(settings)() as session:
        profile = get_published_profile(session, args.slug)
    if profile is None:
        raise SystemExit(f"Published profile not found: {args.slug}")
    path = write_snapshot(settings.snapshot_dir, profile)
    print(f"snapshot generated: {args.slug} ({path.name})")
    return path


if __name__ == "__main__":
    run_snapshot_command()
