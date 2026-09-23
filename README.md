# Career Platform

A database-driven personal resume website built with FastAPI, Jinja templates,
plain CSS, and SQLite.

## Local development

Install the application and development tools:

```bash
pip install -e '.[dev]'
```

Copy `.env.example` to `.env` and set the Resend and contact variables when
contact delivery is configured. Database migrations, seed data, and snapshot
generation will be added in later implementation tasks.

Start the local server:

```bash
uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000
```

Check the application without requiring SQLite or Resend:

```bash
curl -fsS http://localhost:8000/healthz
```

The project is configured for GitHub Codespaces with port `8000` forwarded.