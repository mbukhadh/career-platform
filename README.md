# Career Platform

A database-driven personal resume website built with FastAPI, Jinja templates,
plain CSS, and SQLite.

## Local development

Install the application and development tools:

```bash
pip install -e '.[dev]'
```

Copy `.env.example` to `.env` and set the Resend and contact variables when
contact delivery is configured. Initialize the database and seed the profile:

```bash
alembic upgrade head
python -m app.seed
python -m app.generate_snapshot --slug mj-bukhadhour
```

Snapshots contain only published public content. Generate a new snapshot after
reviewed content changes. If SQLite is unavailable, the web application serves
the latest validated snapshot; if neither source is available, it returns a
service-unavailable response. To restore local SQLite, recreate the database
with `alembic upgrade head` and rerun `python -m app.seed`.

Start the local server:

```bash
uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000
```

Check the application without requiring SQLite or Resend:

```bash
curl -fsS http://localhost:8000/healthz
```

The project is configured for GitHub Codespaces with port `8000` forwarded.

Set `RESEND_API_KEY`, `CONTACT_FROM`, and `CONTACT_TO` in `.env` before testing
contact delivery. Never commit `.env`, SQLite files, snapshots, or provider
credentials.