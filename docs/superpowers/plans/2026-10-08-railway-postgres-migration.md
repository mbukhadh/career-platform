# Railway and PostgreSQL Migration Plan

**Goal:** `mjbukhadhour.com` served by a Railway web service on Railway
PostgreSQL, holding the rows that are on the Azure VM today, with Azure left
running as the rollback.

**Design:** [`docs/superpowers/specs/2026-10-08-railway-postgres-migration-design.md`](../specs/2026-10-08-railway-postgres-migration-design.md)

**Starting point (October 8):** VM and `main` both on `8a069c7`. Site live
over HTTPS from the VM. Railway dashboard setup is MJ's and is not confirmed
yet, so every step marked **Railway** or **Cloudflare** waits for him.

**Rules for the whole plan:**

- Never print or commit passwords, tokens, `.env` contents, or database URLs.
- The agent changes nothing on Railway or Cloudflare. Dashboard steps are MJ's.
- No seed and no sample data on Railway. Rows come from the VM.
- Local development and tests stay on SQLite.
- Azure keeps running.

Each step lists where it runs, what runs, why, how it's checked, and how it's
undone.

---

## 1. Back up the VM database

- [x] **Take a consistent backup on the VM**
  - Where: VM
  - What:
    ```bash
    mkdir -p ~/backups
    sqlite3 ~/career-platform/career_platform.db \
      ".backup '/home/azureuser/backups/career_platform-2026-10-08.db'"
    ```
  - Why: `.backup` takes a consistent copy while the service is running. A
    plain `cp` can catch a write halfway.
  - Check: `sqlite3 ~/backups/career_platform-2026-10-08.db "PRAGMA integrity_check;"`
    prints `ok`, and the row count of every table matches the live file.
  - Undo: delete the backup file. The live database is only read.

- [x] **Copy the backup to the laptop, outside the repo**
  - Where: laptop
  - What:
    ```bash
    mkdir -p ~/career-platform-backups
    scp -i ~/.ssh/isba4775_azure \
      azureuser@135.232.198.204:backups/career_platform-2026-10-08.db \
      ~/career-platform-backups/
    ```
  - Why: the transfer runs from the laptop. Keeping the file outside the
    repo means it can't be committed, whatever `.gitignore` says.
  - Check: SHA-256 of the laptop copy equals the VM copy; `integrity_check`
    is `ok` on the laptop; the profile row reads back with MJ's name.
  - Undo: delete the laptop copy.

- [x] **Record the result** in this plan: both paths, the checksum, and the
  row counts per table.
  - Result (10/8):
    - VM: `/home/azureuser/backups/career_platform-2026-10-08.db`
    - Laptop: `~/career-platform-backups/career_platform-2026-10-08.db`
      (outside the repo, readable only by me)
    - SHA-256 on both: `d32776cc…cd4f63`. `integrity_check` is `ok` on both.
      Schema version `0001_initial_schema`.
    - Rows, identical in the live file and the backup: owners 1, profiles 1,
      experiences 1, experience_accomplishments 0, education 1,
      skill_groups 1, skills 2, projects 1, contact_configurations 1.
    - Read back from the laptop copy: my profile, Python and SQL, Career
      Platform, the B.S. program, and the experience placeholder.

## 2. Code changes (no Railway access needed)

Work on `main`, one commit per task, tests green before each commit.

- [x] **2.1 Add the PostgreSQL driver**
  - Where: laptop
  - What: `uv add "psycopg[binary]>=3.2,<4"` (updates `pyproject.toml` and
    `uv.lock`).
  - Why: nothing installed today can connect to PostgreSQL.
  - Check: `uv run python -c "import psycopg"` succeeds; `uv run pytest -q`
    passes.
  - Undo: `uv remove psycopg`.

- [x] **2.2 Normalize the database URL in `Settings`**
  - Where: `app/config.py`, new `tests/test_config.py`
  - What: test first, then:
    ```python
    from pydantic import field_validator

    def normalize_database_url(url: str) -> str:
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix):]
        return url

    class Settings(BaseSettings):
        ...
        @field_validator("database_url")
        @classmethod
        def _use_psycopg_driver(cls, value: str) -> str:
            return normalize_database_url(value)
    ```
  - Why: Railway's URL starts with `postgresql://`, which SQLAlchemy sends to
    a driver that isn't installed. One rewrite, in the one place every
    caller reads the URL from.
  - Check: tests assert `postgres://…` and `postgresql://…` become
    `postgresql+psycopg://…`, and that SQLite and already-normalized URLs
    pass through unchanged. Test URLs use made-up hosts and no real password.
  - Undo: revert the commit.

- [x] **2.3 One engine per process, with a connect timeout**
  - Where: `app/db.py`, new `tests/test_db.py`
  - What:
    ```python
    from functools import lru_cache

    @lru_cache
    def _engine_for(database_url: str) -> Engine:
        if database_url.startswith("postgresql"):
            return create_engine(
                database_url,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 5},
            )
        return create_engine(database_url, future=True)

    def get_engine(settings: Settings) -> Engine:
        return _engine_for(settings.database_url)
    ```
  - Why: today every page load builds a new engine. On PostgreSQL that leaks
    connections until the server refuses more. The timeout makes a dead
    database fail in 5 seconds so the fallback page can run.
  - Check: a test asserts two calls with the same settings return the same
    engine object; existing tests pass.
  - Undo: revert the commit.

- [x] **2.4 Make Alembic use the app's URL**
  - Where: `migrations/env.py`, new `tests/test_migrations.py`
  - What: replace the `alembic.ini` lookups with `get_settings().database_url`
    in both offline and online modes; build the online engine with
    `create_engine(url, poolclass=pool.NullPool)`.
  - Why: `alembic.ini` is hardcoded to the SQLite file, so on Railway the
    migration would build a SQLite file in the container and leave
    PostgreSQL empty.
  - Check: a test sets `DATABASE_URL` to a SQLite file in a temp folder, runs
    `alembic upgrade head` through Alembic's API, and asserts the `profiles`
    table and the `alembic_version` row exist in that file and that
    `./career_platform.db` was not touched.
  - Undo: revert the commit.

- [x] **2.5 Add `railway.json`**
  - Where: repo root
  - What:
    ```json
    {
      "$schema": "https://railway.com/railway.schema.json",
      "deploy": {
        "preDeployCommand": ["alembic upgrade head"],
        "startCommand": "uvicorn app.main:create_app --factory --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'",
        "healthcheckPath": "/healthz",
        "restartPolicyType": "ON_FAILURE"
      }
    }
    ```
  - Why: this is the start command, the port binding, the proxy-header trust,
    and the migration step, kept in Git instead of typed into a dashboard.
    There is no seed command in it. Field names were checked against
    Railway's published schema on October 8.
  - Check: the file is valid JSON; locally,
    `PORT=8765 sh -c "<the start command>"` serves the page, and a request
    with `X-Forwarded-Proto: https` returns a stylesheet link that starts
    with `https://`.
  - Undo: delete the file.

- [x] **2.6 Prove a page loads when the database is down**
  - Where: new test in `tests/routes/`
  - What: build the app with `DATABASE_URL` pointing at a SQLite path in a
    folder that doesn't exist and an empty snapshot folder; request `/`.
  - Why: this is the behaviour the guide asks for. It exists already; the
    test keeps it.
  - Check: status 503, the body is the "service unavailable" template with
    the stylesheet link, and `/healthz` still returns 200.
  - Undo: delete the test.

- [x] **2.7 Transfer and compare script**
  - Where: new `app/transfer.py` (run as `python -m app.transfer`), new
    `tests/test_transfer.py`
  - What:
    - `python -m app.transfer --source <backup.db>` copies every table in
      foreign-key order (`Base.metadata.sorted_tables`) into the database
      named by `RAILWAY_DATABASE_URL`, in one transaction.
    - It stops with a clear message if `RAILWAY_DATABASE_URL` is missing, if
      the target has no tables (migrations haven't run), or if any target
      table already has rows.
    - `python -m app.transfer --source <backup.db> --compare` prints, per
      table, source rows, target rows, and whether a SHA-256 over every row
      (ordered by id, dates as ISO text) matches. `--write <file>` saves that
      table as Markdown.
    - It reads the URL from the environment or the local `.env` and never
      prints it, including in error messages.
  - Why: copying through SQLAlchemy converts SQLite's text dates and 0/1
    booleans into real PostgreSQL types. A count alone doesn't prove the
    content moved, so the comparison hashes the rows too.
  - Check: tests copy a seeded SQLite file into an empty SQLite file and
    assert counts and hashes match; assert a second run refuses; assert a
    changed row is reported as a mismatch; assert the URL never appears in
    output.
  - Undo: delete the two files.

- [x] **2.8 Push**
  - Where: laptop
  - What: `uv run pytest -q`, `uv run ruff check .`, then push `main`.
  - Check: `git status` shows no `.env`, `.db`, or backup file staged;
    `origin/main` equals local `main`. Record the commit hash here.
  - Result (10/8): code and tests pushed to `main` as `d4bee5f`. 28 tests
    pass and `ruff check` is clean. No `.env`, database, or backup file is in
    the commit.
  - Note: the VM is not redeployed in this step. If it later pulls `main`,
    run `uv sync --locked --no-dev` before restarting, because the lock file
    changed.

**Results for section 2 (10/8), before pushing:**

- `psycopg` 3.3.6 installed from the lock file.
- 28 tests pass (12 before, 16 new); `ruff check` is clean.
- The Railway start command, run locally with `PORT` set, serves the page.
  With `X-Forwarded-Proto: https` the stylesheet link is `https://…`;
  without it, `http://…`.
- With `DATABASE_URL` set to a PostgreSQL address that can't be reached, the
  page returns the "Temporarily unavailable" page with status 503 in 5.1
  seconds, styled, and `/healthz` still returns 200.
- With the same URL, `alembic upgrade head` fails trying to reach PostgreSQL
  through psycopg, which shows it no longer uses the SQLite path in
  `alembic.ini`.
- Not tested: a real PostgreSQL server. The first one is Railway's.

## 3. Deploy on Railway — MJ, in the dashboard

- [ ] **Railway: confirm section 2 of the guide is done** (Postgres online,
  TCP Proxy on, `RAILWAY_DATABASE_URL` in the local `.env`, web service added
  with `DATABASE_URL` pointing at Postgres).
- [ ] **Railway: click Deploy, then Generate Domain.**
- [ ] **What to look for:**

| Look at | Expected | If not |
| --- | --- | --- |
| Build log | Python 3.12 or 3.13, packages installed from `uv.lock`, `psycopg` among them | Tell the agent the version or the error |
| Deploy log, before the app starts | `alembic upgrade head` and `Running upgrade -> 0001_initial_schema` | `command not found`: agent switches to `python -m alembic` |
| Deploy log, app start | `Uvicorn running on http://0.0.0.0:8080` (the port is inside the container) | Paste the error |
| The generated domain, no port | The "not found" page, **with styles**, because the tables are empty | Unstyled: the proxy flag isn't in effect. A default profile showing: something seeded; stop. |
| `<generated domain>/healthz` | `{"status":"ok"}` | Service isn't up |

## 4. Move the rows

- [ ] **Transfer**
  - Where: laptop
  - What: `uv run python -m app.transfer --source ~/career-platform-backups/career_platform-2026-10-08.db`
  - Why: the rows on the VM are the site's content. They are copied, not
    recreated.
  - Check: the script reports the rows copied per table, matching the backup
    counts from section 1.
  - Undo: the copy is one transaction, so a failure leaves the target empty.
    To redo after a success, MJ empties the tables in Railway.
  - If it times out on campus Wi-Fi: rerun from a phone hotspot.

- [ ] **Compare**
  - Where: laptop
  - What: the same command with `--compare --write docs/evidence/railway-data-comparison.md`
  - Check: every table shows equal counts and a content match. The saved
    file contains no host, user, password, or URL.

- [ ] **Read the page** at the Railway domain: MJ's name, headline,
  education, project, and the two skills, and the footer says
  "Profile source: database".

## 5. Domain — MJ, by hand

The agent does not touch Railway or Cloudflare here.

- [ ] **Before changing anything:** the current `@` record is an **A record
  at `135.232.198.204`**. Write it down; it's the rollback.
- [ ] **Railway:** Custom Domain, `mjbukhadhour.com` only.
- [ ] **Cloudflare:** change `@` from the A record to a CNAME at Railway's
  target, DNS only (grey cloud). Add Railway's TXT record. Leave `www` and
  every other record alone. Note the time.
- [ ] **Check:** `https://mjbukhadhour.com` shows a valid certificate for the
  domain and MJ's data. Pending DNS or TLS is pending, not done.

## 6. After cutover (separate steps, not part of this plan's code)

Cloudflare and Railway CLIs, the test skill, the push-to-deploy proof, the
README, `docs/project-1-submission.md`, and removing the TCP Proxy.

## Rollback for the whole plan

1. **Domain:** set `@` back to an A record at `135.232.198.204`.
2. **Code:** revert the section 2 commits and push. The VM never needed them.
3. **Data:** if Railway has taken writes since the transfer, compare both
   databases before pointing the domain back, or those writes are lost.

The VM, nginx, its certificate, and its database are not changed by any step
here except the read-only backup.
