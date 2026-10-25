# Database failure and recovery (local reproduction)

Date: 2026-10-25, 23:26–23:28 UTC. Run on my laptop on branch
`feat/projects-unavailable` (uncommitted working tree on top of `53fcead`),
with Claude Code running the commands. Local SQLite only. A PostgreSQL outage
on Railway was **not** tested.

## What the page does now

| Situation | Status | Page |
| --- | --- | --- |
| Healthy | 200 | Profile and projects; footer `Projects source: database` |
| Projects table empty | 200 | Profile and "No projects published yet." |
| Projects query fails | 503 | Profile still shown and "Projects temporarily unavailable". No projects, no cached or sample content |
| Database back | 200 on the next request | Projects again, no restart |

The profile (name, introduction, education, skills, links) is in
`app/profile_content.py`, so it doesn't depend on the database. Projects are
read from the database on every request (`get_published_projects`). The old
snapshot fallback and the full-page "Temporarily unavailable" were removed.

## Run 1: found a stuck connection (before the fix)

Same steps as run 2. Steps 1–3 behaved as expected (503, then 200 after
creating the database). But after the database folder was moved away, the
same server still answered `HTTP 200` with the Career Platform project.
SQLAlchemy's default pool for a SQLite file kept a connection open, and that
connection still pointed at the moved file. So the page hid the fact that the
database at the configured path was gone.

Fix: file-based SQLite now uses `NullPool` (`app/db.py`), so each request
opens the file again. PostgreSQL keeps its pool, with `pool_pre_ping=True` to
drop dead connections and a 5-second connect timeout. A new test,
`test_database_removed_after_healthy_request_is_reported`, failed with the old
`app/db.py` and passes with the fix.

## Run 2: after the fix

One server process, started once and never restarted:
`uv run uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8765`,
with `DATABASE_URL=sqlite:///<scratch>/data/career.db`, where `<scratch>` is
a temporary folder outside the repo. The body lines are `grep -oE` matches for
the `<h1>`, the project heading and the two messages.

```text
Started 2026-10-25 23:27:38 UTC. One server process, PID 93636, never restarted.

### 1. Database missing (23:27:38 UTC)
$ ls <scratch>/data
ls: <scratch>/data: No such file or directory
$ curl -s -w "HTTP %{http_code}\n" http://127.0.0.1:8765/
HTTP 503
<h1>Mohammad (MJ) Bukhadhour</h1>
Projects temporarily unavailable
$ curl -s http://127.0.0.1:8765/healthz
{"status":"ok"}

### 2. Create an empty database (schema only) (23:27:38 UTC)
$ mkdir <scratch>/data && uv run alembic upgrade head
exit 0
$ curl …/
HTTP 200
<h1>Mohammad (MJ) Bukhadhour</h1>
No projects published yet.
Projects source: database

### 3. Add the seed rows (23:27:39 UTC)
$ uv run python -m app.seed
exit 0
$ curl …/
HTTP 200
<h1>Mohammad (MJ) Bukhadhour</h1>
<h3>Career Platform</h3>
Projects source: database

### 4. Move the database away (23:27:39 UTC)
$ mv <scratch>/data <scratch>/data-away
$ curl …/
HTTP 503
<h1>Mohammad (MJ) Bukhadhour</h1>
Projects temporarily unavailable

### 5. Put it back (23:27:39 UTC)
$ mv <scratch>/data-away <scratch>/data
$ curl …/
HTTP 200
<h1>Mohammad (MJ) Bukhadhour</h1>
<h3>Career Platform</h3>
Projects source: database

$ lsof -ti tcp:8765 -sTCP:LISTEN   (same PID as at start)
93636

### Server log
INFO:     127.0.0.1:61987 - "GET /healthz HTTP/1.1" 200 OK
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file
INFO:     127.0.0.1:61988 - "GET / HTTP/1.1" 503 Service Unavailable
INFO:     127.0.0.1:61989 - "GET /healthz HTTP/1.1" 200 OK
INFO:     127.0.0.1:61991 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:61992 - "GET / HTTP/1.1" 200 OK
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file
INFO:     127.0.0.1:61993 - "GET / HTTP/1.1" 503 Service Unavailable
INFO:     127.0.0.1:61994 - "GET / HTTP/1.1" 200 OK
```

The process ID is the same at the start and the end, so recovery needed no
restart.

## Tests

`tests/routes/test_projects_database.py` covers healthy (200), empty (200),
failure (503, profile visible, message), recovery on the next request, and
removal after a healthy request.

```text
$ uv run pytest -q          # 2026-10-25 23:27:18 UTC
34 passed, 238 warnings in 0.56s
```

## Not tested

- A real PostgreSQL outage on Railway. I can't stop Railway's database from
  here, and doing it on the live site would take the projects down.
- The 5-second PostgreSQL connect timeout. It was measured on 2026-10-08 with
  an unreachable address (5.1 s; Railway plan §2 results), not re-measured.
