import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.models import Base
from app.seed import seed_database
from app.transfer import compare_tables, copy_tables, main, render_markdown


@pytest.fixture
def source(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'source.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)
        session.commit()
    return engine


@pytest.fixture
def target(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'target.db'}")
    Base.metadata.create_all(engine)
    return engine


def test_copy_moves_every_row_and_content_matches(source, target):
    copied = copy_tables(source, target)

    assert copied["profiles"] == 1
    assert copied["skills"] == 2
    results = compare_tables(source, target)
    assert all(item.source_rows == item.target_rows for item in results)
    assert all(item.content_matches for item in results)


def test_copy_refuses_a_target_that_already_has_rows(source, target):
    copy_tables(source, target)
    with pytest.raises(SystemExit, match="already has rows"):
        copy_tables(source, target)


def test_copy_refuses_a_target_without_tables(source, tmp_path):
    empty = create_engine(f"sqlite:///{tmp_path / 'empty.db'}")
    with pytest.raises(SystemExit, match="Run the migrations"):
        copy_tables(source, empty)


def test_compare_reports_changed_content(source, target):
    copy_tables(source, target)
    with target.begin() as connection:
        connection.execute(text("update skills set name = 'Changed' where name = 'SQL'"))

    by_table = {item.table: item for item in compare_tables(source, target)}
    assert by_table["skills"].source_rows == by_table["skills"].target_rows
    assert by_table["skills"].content_matches is False
    assert by_table["profiles"].content_matches is True
    assert "| `skills` | 2 | 2 | NO |" in render_markdown(list(by_table.values()))


def test_command_never_prints_the_target_url(source, target, tmp_path, monkeypatch, capsys):
    target_url = f"sqlite:///{tmp_path / 'target.db'}"
    monkeypatch.setenv("RAILWAY_DATABASE_URL", target_url)
    report = tmp_path / "comparison.md"
    backup = str(tmp_path / "source.db")

    assert main(["--source", backup]) == 0
    assert main(["--source", backup, "--compare", "--write", str(report)]) == 0

    output = capsys.readouterr()
    assert "target.db" not in output.out + output.err
    assert "target.db" not in report.read_text()
    assert "all tables match" in output.out


def test_command_stops_without_a_target(source, tmp_path, monkeypatch):
    monkeypatch.delenv("RAILWAY_DATABASE_URL", raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit, match="RAILWAY_DATABASE_URL is not set"):
        main(["--source", str(tmp_path / "source.db")])
