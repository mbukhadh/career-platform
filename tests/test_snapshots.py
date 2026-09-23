from app.domain.public_profile import PublishedProfile
from app.snapshots import (
    load_profile_with_fallback,
    read_latest_snapshot,
    write_snapshot,
)


def profile():
    return PublishedProfile(
        slug="jane-doe",
        name="Jane Doe",
        headline="Engineer",
        summary="Summary",
        location=None,
    )


def test_database_failure_serves_last_known_good_snapshot(tmp_path):
    write_snapshot(tmp_path, profile())

    result, source = load_profile_with_fallback(
        "jane-doe",
        db_loader=lambda: (_ for _ in ()).throw(ConnectionError("sqlite down")),
        snapshot_dir=tmp_path,
    )

    assert source == "snapshot"
    assert result.slug == "jane-doe"


def test_invalid_snapshot_does_not_replace_valid_snapshot(tmp_path):
    valid_path = write_snapshot(tmp_path, profile())
    invalid_path = tmp_path / "jane-doe-v999.json"
    invalid_path.write_text('{"slug":"jane-doe","experiences":null}')

    assert read_latest_snapshot(tmp_path, "jane-doe").slug == "jane-doe"
    assert valid_path.exists()
    assert read_latest_snapshot(tmp_path, "jane-doe").slug == profile().slug
