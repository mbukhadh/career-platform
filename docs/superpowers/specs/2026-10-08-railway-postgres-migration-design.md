# Move the site to Railway and PostgreSQL: design

Date: October 8, 2026 · Status: draft, waiting for MJ's approval

## Goal

Run `mjbukhadhour.com` from a Railway web service backed by Railway
PostgreSQL, with the rows that are on the Azure VM today, and with Azure left
running as the place to go back to.

Done means:

- Railway serves the same commit as `main`, with the schema created by
  `alembic upgrade head` and no seed step.
- Every table on Railway has the same row count and the same content as the
  VM's SQLite database.
- `https://mjbukhadhour.com` loads from Railway with a valid certificate,
  styles included.
- Local development and the tests still run on SQLite with no extra setup.

## Where things stand (inspected October 8)

| | |
| --- | --- |
| App | FastAPI app factory `app.main:create_app`, Jinja templates, plain CSS |
| Running on | Azure VM, commit `8a069c7`, Uvicorn on `127.0.0.1:8000` behind nginx, Python 3.12.3 |
| Database | SQLite file `career_platform.db` in the repo folder on the VM |
| Rows on the VM | owners 1, profiles 1, experiences 1, experience_accomplishments 0, education 1, skill_groups 1, skills 2, projects 1, contact_configurations 1 |
| Schema | One Alembic revision, `0001_initial_schema`, which calls `Base.metadata.create_all` |
| Railway | Project exists. Postgres and the web service are MJ's to set up by hand; not verified from here. |

What the code already does right:

- `DATABASE_URL` is read from the environment (`app/config.py`). The default
  is the local SQLite file.
- The models use portable column types (strings, text, dates, booleans,
  integers), so the same schema builds on PostgreSQL.
- When the database fails, the profile page falls back to a saved snapshot,
  and to a "temporarily unavailable" page when there is no snapshot.
- `/healthz` does not touch the database.

What has to change:

1. **No PostgreSQL driver.** Nothing in `pyproject.toml` can talk to Postgres.
2. **Alembic ignores `DATABASE_URL`.** `migrations/env.py` reads the URL from
   `alembic.ini`, which is hardcoded to the SQLite file. On Railway,
   `alembic upgrade head` would create a SQLite file inside the container and
   leave Postgres empty. This is the "relation profiles does not exist"
   failure the guide warns about.
3. **A new engine per request.** `get_session_factory` builds a new SQLAlchemy
   engine on every page load. SQLite tolerates that. On Postgres each engine
   opens its own connections, and they pile up until the server refuses more.
4. **No start command.** Railway doesn't know to run
   `app.main:create_app` as a factory, on `0.0.0.0`, on its `PORT`.
5. **Forwarded protocol isn't trusted.** `base.html` builds an absolute
   stylesheet URL from the request. Behind Railway's proxy the request reaches
   Uvicorn as plain HTTP, so the link comes out as `http://…` and the browser
   blocks it on an HTTPS page. Uvicorn only trusts `X-Forwarded-Proto` from
   `127.0.0.1` by default, which is why it works behind nginx on the VM and
   won't on Railway.
6. **No connection timeout.** If Postgres is unreachable, a page request can
   hang instead of falling back.

## Decisions

### 1. Driver: psycopg 3

Add `psycopg[binary]`. Railway hands out URLs that start with
`postgresql://`, which SQLAlchemy would send to the older psycopg2 driver, so
`Settings` rewrites `postgres://` and `postgresql://` to
`postgresql+psycopg://` in one place. The app, Alembic, and the transfer
script all get the URL from there.

Considered: `psycopg2-binary`, which needs no rewrite. Not chosen because it
is in maintenance mode and psycopg 3 is the supported driver.

### 2. One engine per process

`app/db.py` caches the engine by URL. For PostgreSQL it adds
`pool_pre_ping=True` (drop dead connections before using them) and a
5-second connect timeout. SQLite gets the engine it has today.

### 3. Alembic reads the same URL as the app

`migrations/env.py` takes the URL from `get_settings()`. `alembic.ini` keeps
its SQLite line as documentation of the local default, but nothing reads it.

### 4. Railway configuration lives in the repo

A `railway.json` at the repo root:

- **Pre-deploy command:** `alembic upgrade head`. It runs before the new
  version takes traffic, and a failed migration fails the deploy instead of
  replacing a working one. It shows in the deploy log.
- **Start command:** `uvicorn app.main:create_app --factory --host 0.0.0.0
  --port $PORT --proxy-headers --forwarded-allow-ips='*'`.
- **Health check:** `/healthz`.

`--forwarded-allow-ips='*'` trusts the forwarded headers from any address.
That is safe on Railway because the container is only reachable through
Railway's proxy. It is not used on the VM, whose systemd unit is unchanged.
A side benefit: the contact form's rate limiter sees the visitor's address,
not the proxy's.

No seed command appears anywhere in `railway.json`.

### 5. Data moves by a one-time transfer script, run from the laptop

`scripts/transfer_to_postgres.py`:

- Reads a **backup copy** of the VM's SQLite file, never the live file.
- Reads the target from `RAILWAY_DATABASE_URL` in the local `.env`. It never
  prints the URL.
- Copies every table in foreign-key order inside one transaction, through
  SQLAlchemy, so SQLite's text dates and 0/1 booleans become real PostgreSQL
  dates, timestamps, and booleans. Primary keys are copied as they are.
- Refuses to run if any target table already has rows, so it can't double up
  or overwrite.
- Has a `--compare` mode that prints, per table, the row count on each side
  and whether the content matches (a hash of every row, ordered by id), and
  can write that table to `docs/evidence/` with no connection details in it.

Considered: `pgloader`, or dumping SQL from SQLite and replaying it. Not
chosen because both need type fixes by hand for booleans and dates, and
neither gives the content comparison.

### 6. A page still loads when the database is down

Unchanged behaviour, made reliable: with the connect timeout, a dead database
fails in about 5 seconds and the existing fallback runs. On Railway there is
no saved snapshot (the folder is ignored by Git and the container's disk is
rebuilt on every deploy), so the visitor sees the "temporarily unavailable"
page with status 503, styled, not a hang or a stack trace. A test covers it.

Not doing now: generating a snapshot at startup on Railway so the profile
itself survives an outage. It would go stale after every database edit until
the next deploy. Worth revisiting if the site stays on Railway.

### 7. Local development stays on SQLite

No local PostgreSQL and no Codespaces. The default `DATABASE_URL` is
unchanged, and the tests run on SQLite. The transfer and compare logic is
tested SQLite to SQLite. The PostgreSQL path is first exercised on Railway.

## How the migration runs

```
Azure VM                         Laptop                           Railway
career_platform.db  ──backup──▶  ~/career-platform-backups/  ──▶  Postgres
(stays live)                     (outside the repo)   transfer    (schema from Alembic)
```

1. Back up the VM database and copy the backup to the laptop, outside Git.
2. Code tasks, commit, push. Nothing on Railway is touched.
3. MJ deploys on Railway and generates the Railway domain. Before the
   transfer the site shows the "not found" page, with styles, because the
   tables exist and are empty.
4. Transfer, then compare, then read the page on the Railway domain.
5. MJ moves the root domain's DNS by hand.

## What MJ does by hand

- All Railway dashboard work: Postgres, TCP Proxy, the web service,
  `DATABASE_URL` on it, Deploy, Generate Domain, Custom Domain.
- All Cloudflare changes.
- Removing the TCP Proxy at the end.

## Risks and what happens then

| Risk | What it looks like | Response |
| --- | --- | --- |
| The PostgreSQL path is untested until Railway | Deploy or pre-deploy fails | Read the log; fix and push. Azure is still serving the domain. |
| `alembic` or `uvicorn` not found in Railway's start environment | "command not found" in the log | Switch both to `python -m alembic` and `python -m uvicorn`. |
| Campus Wi-Fi blocks the database's public port | Transfer times out | Run the transfer from a phone hotspot. |
| Railway picks a different Python than tested (3.12 on the VM, 3.13 locally) | Build log shows another version | Add a `.python-version` file. |
| `www.mjbukhadhour.com` still points at Azure | `www` shows the VM's data after writes go to Railway | Expected; the trial allows one custom domain. Noted in the README. |

## Rollback

- **Code:** revert the commit and push.
- **Domain:** put the `@` record back to an A record at `135.232.198.204`.
  The VM, nginx, and its certificate are untouched by this plan. Its
  certificate for the root name can't renew while DNS points at Railway, and
  expires January 4, 2027.
- **Data:** going back is only clean until Railway takes its first write.
  After that the two databases differ, so pause writes and compare both
  before switching DNS back.

## Out of scope

- Contact form email delivery (no provider key on the VM; the same on Railway).
- Design changes.
- Stopping or changing the Azure VM.
- The README and `docs/project-1-submission.md`, which come after cutover.
