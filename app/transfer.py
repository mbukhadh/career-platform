"""Copy a SQLite backup into an empty PostgreSQL database, then compare them.

    python -m app.transfer --source backup.db
    python -m app.transfer --source backup.db --compare --write comparison.md

The target is read from RAILWAY_DATABASE_URL (environment or .env) and is
never printed.
"""

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.config import normalize_database_url
from app.models import Base

TABLES = Base.metadata.sorted_tables


class TransferSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    railway_database_url: str = ""


@dataclass(frozen=True)
class TableComparison:
    table: str
    source_rows: int
    target_rows: int
    content_matches: bool


def _row_count(engine: Engine, table) -> int:
    with engine.connect() as connection:
        return connection.scalar(select(func.count()).select_from(table)) or 0


def _require_schema(target: Engine) -> None:
    existing = set(inspect(target).get_table_names())
    missing = [table.name for table in TABLES if table.name not in existing]
    if missing:
        raise SystemExit(
            "Target is missing tables ("
            + ", ".join(missing)
            + "). Run the migrations there first."
        )


def copy_tables(source: Engine, target: Engine) -> dict[str, int]:
    """Copy every table in foreign-key order, in one transaction."""
    _require_schema(target)
    occupied = [table.name for table in TABLES if _row_count(target, table)]
    if occupied:
        raise SystemExit(
            "Target already has rows in: "
            + ", ".join(occupied)
            + ". Nothing was copied."
        )

    copied: dict[str, int] = {}
    with source.connect() as reader, target.begin() as writer:
        for table in TABLES:
            rows = [dict(row._mapping) for row in reader.execute(select(table))]
            if rows:
                writer.execute(table.insert(), rows)
            copied[table.name] = len(rows)
    return copied


def _comparable(value: object) -> object:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _table_digest(engine: Engine, table) -> tuple[int, str]:
    order = list(table.primary_key.columns)
    with engine.connect() as connection:
        rows = [
            [_comparable(value) for value in row]
            for row in connection.execute(select(table).order_by(*order))
        ]
    payload = json.dumps(rows, sort_keys=True, default=str).encode()
    return len(rows), hashlib.sha256(payload).hexdigest()


def compare_tables(source: Engine, target: Engine) -> list[TableComparison]:
    _require_schema(target)
    results = []
    for table in TABLES:
        source_rows, source_digest = _table_digest(source, table)
        target_rows, target_digest = _table_digest(target, table)
        results.append(
            TableComparison(
                table=table.name,
                source_rows=source_rows,
                target_rows=target_rows,
                content_matches=source_digest == target_digest,
            )
        )
    return results


def render_markdown(results: list[TableComparison]) -> str:
    lines = [
        "| Table | VM backup rows | Railway rows | Content matches |",
        "| --- | --- | --- | --- |",
    ]
    for item in results:
        verdict = "yes" if item.content_matches else "NO"
        lines.append(
            f"| `{item.table}` | {item.source_rows} | {item.target_rows} | {verdict} |"
        )
    return "\n".join(lines) + "\n"


def _target_engine() -> Engine:
    url = TransferSettings().railway_database_url
    if not url:
        raise SystemExit("RAILWAY_DATABASE_URL is not set. Add it to .env.")
    return create_engine(
        normalize_database_url(url),
        hide_parameters=True,
        connect_args={"connect_timeout": 10} if url.startswith("postgres") else {},
    )


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", required=True, type=Path, help="SQLite backup")
    parser.add_argument("--compare", action="store_true", help="compare, don't copy")
    parser.add_argument("--write", type=Path, help="save the comparison as Markdown")
    args = parser.parse_args(arguments)

    if not args.source.is_file():
        raise SystemExit(f"Backup not found: {args.source}")
    source = create_engine(f"sqlite:///{args.source}")
    target = _target_engine()

    try:
        if not args.compare:
            copied = copy_tables(source, target)
            for name, rows in copied.items():
                print(f"copied {rows:>3} rows  {name}")
            print(f"total  {sum(copied.values()):>3} rows")
            return 0

        results = compare_tables(source, target)
    except SQLAlchemyError as error:
        # Driver messages can include the host, so only the error type is shown.
        raise SystemExit(f"Database error: {type(error).__name__}") from None

    table = render_markdown(results)
    print(table, end="")
    if args.write:
        args.write.write_text(table, encoding="utf-8")
        print(f"saved to {args.write}")
    matched = all(
        item.source_rows == item.target_rows and item.content_matches
        for item in results
    )
    print("all tables match" if matched else "MISMATCH")
    return 0 if matched else 1


if __name__ == "__main__":
    raise SystemExit(main())
