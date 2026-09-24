from app.domain.public_profile import PublishedProfile
from app.snapshots import (
    load_profile_with_fallback,
    read_latest_snapshot,
    write_snapshot,
)


def profile():
    return PublishedProfile(
        slug="mj-bukhadhour",
        name="Mohammad (MJ) Bukhadhour",
        headline="Engineer",
        summary="Summary",
        location=None,
    )


def test_database_failure_serves_last_known_good_snapshot(tmp_path):
    write_snapshot(tmp_path, profile())

    result, source = load_profile_with_fallback(
        "mj-bukhadhour",
        db_loader=lambda: (_ for _ in ()).throw(ConnectionError("sqlite down")),
        snapshot_dir=tmp_path,
    )

    assert source == "snapshot"
    assert result.slug == "mj-bukhadhour"


def test_invalid_snapshot_does_not_replace_valid_snapshot(tmp_path):
    valid_path = write_snapshot(tmp_path, profile())
    invalid_path = tmp_path / "mj-bukhadhour-v999.json"
    invalid_path.write_text('{"slug":"mj-bukhadhour","experiences":null}')

    assert read_latest_snapshot(tmp_path, "mj-bukhadhour").slug == "mj-bukhadhour"
    assert valid_path.exists()
    assert read_latest_snapshot(tmp_path, "mj-bukhadhour").slug == profile().slug
