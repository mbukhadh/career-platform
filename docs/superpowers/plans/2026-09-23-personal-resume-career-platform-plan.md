# Personal Resume Website and Career Platform Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a database-driven, public personal resume site with a resilient SQLite-backed content model, a public-safe snapshot fallback, and a protected Resend contact form that can later grow into a career platform.

**Architecture:** Use a FastAPI application with Jinja templates and plain CSS. Keep domain models, repository queries, snapshot generation/reading, contact delivery, and route rendering in focused modules. Store structured content in SQLite, render only published public data, and maintain an atomically replaced versioned JSON snapshot so the public profile remains available when SQLite cannot be read.

**Tech Stack:** Python 3.12+, FastAPI, Uvicorn, Jinja2, SQLAlchemy 2.x, Alembic, SQLite, Pydantic, Resend Python SDK or HTTPS API client, pytest, httpx, and plain CSS. Run locally in GitHub Codespaces.

**Spec:** `docs/superpowers/specs/2026-09-23-personal-resume-career-platform-design.md`

## Global Constraints

- The public profile remains viewable using a versioned last-known-good snapshot when the database is unavailable; the fallback must not expose drafts or protected contact details.
- Contact details are not rendered in the initial public HTML or exposed in unauthenticated API responses.
- The initial owner is the only content editor; updates happen through reviewed code changes, migrations, or seed data.
- Unpublished, draft, archived, and private records are never included in public queries or page output.
- Snapshot generation must use the same published-content boundary, must exclude protected contact configuration, and must fail without replacing the existing snapshot if validation fails.
- Snapshot reads must be independent of the unavailable database and must be atomic so visitors never receive a partially written snapshot.
- If neither the database nor a valid snapshot is available, return a deliberate service-unavailable response rather than an empty or success-shaped page.
- Do not log message bodies or protected destination details.
- Contact delivery must fail closed: never claim a message was delivered when the provider rejected it.
- The public site must provide semantic landmarks and headings, keyboard operation, visible focus states, descriptive link names, meaningful alt text, and contact-submission status messaging.
- The implementation must use FastAPI with Jinja templates, plain CSS, SQLite, local Codespaces deployment, and Resend contact delivery.
- Structured project summaries are included in the first release; long-form case studies remain out of scope.

## Review Focus

- A database read timeout or connection failure must serve the last validated public snapshot rather than an empty page or a database error.
- A malformed, incomplete, or private snapshot must be rejected without replacing the prior valid snapshot.
- A concurrent snapshot write/read must never expose partial JSON.
- A published profile with no experience, education, skills, or projects must render valid empty states without crashing.
- Contact input containing invalid email, oversized fields, or abuse attempts must be rejected without calling Resend or leaking the destination address.

---

### Task 1: Establish the FastAPI application and Codespaces development shell

**Files:**
- Create: `pyproject.toml`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `app/config.py`
- Create: `templates/base.html`
- Create: `templates/errors/service-unavailable.html`
- Create: `static/css/site.css`
- Create: `.devcontainer/devcontainer.json`
- Create: `.env.example`
- Create: `tests/test_health.py`
- Modify: `README.md`

**Interfaces:**
- Produces `app.main:create_app() -> FastAPI`.
- Produces `app.config.Settings` with `database_url`, `snapshot_dir`, `resend_api_key`, `contact_from`, `contact_to`, and `environment`.
- Provides `GET /healthz` returning `{"status": "ok"}` without requiring the database.

- [ ] **Step 1: Write the failing application smoke test**

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_does_not_require_database():
    client = TestClient(create_app())
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_health.py -q`

Expected: FAIL because the application factory and health route do not yet exist.

- [ ] **Step 3: Implement the application shell**

Create the settings object with environment-variable loading and safe local defaults. Mount `static/`, configure Jinja templates, add `create_app()`, and register `/healthz`. Do not connect to SQLite during application import or health checks.

- [ ] **Step 4: Add Codespaces and local configuration**

Configure the devcontainer to install the project in editable mode, expose port `8000`, and run `uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000`. Document `pytest`, `uvicorn`, database initialization, snapshot generation, and required Resend environment variables in `README.md`. Keep `.env.example` free of real credentials.

- [ ] **Step 5: Run the test to verify it passes**

Run: `pytest tests/test_health.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml app templates static .devcontainer .env.example tests/test_health.py README.md
git commit -m "feat: establish FastAPI application shell"
```

**Done looks like:** A fresh Codespaces environment can install the project, start FastAPI on port 8000, and answer `/healthz` even if SQLite and Resend are unavailable.

**How to check:** Run `pip install -e '.[dev]'`, then `uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000` and request `curl -fsS http://127.0.0.1:8000/healthz`; run `pytest tests/test_health.py -q`.

### Task 2: Create the SQLite schema, migrations, and deterministic seed data

**Files:**
- Create: `app/db.py`
- Create: `app/models.py`
- Create: `alembic.ini`
- Create: `migrations/env.py`
- Create: `migrations/versions/0001_initial_schema.py`
- Create: `app/seed.py`
- Create: `tests/test_schema.py`

**Interfaces:**
- Produces `get_engine(settings: Settings) -> Engine`.
- Produces SQLAlchemy models `Owner`, `Profile`, `Experience`, `ExperienceAccomplishment`, `Education`, `SkillGroup`, `Skill`, `Project`, and `ContactConfiguration`.
- Produces `seed_database(session: Session) -> None`.

- [ ] **Step 1: Write schema and seed tests**

```python
def test_seed_creates_one_published_profile_with_ordered_content(session):
    seed_database(session)
    profile = session.query(Profile).filter_by(slug="jane-doe").one()
    assert profile.is_published is True
    assert [item.display_order for item in profile.projects] == sorted(
        item.display_order for item in profile.projects
    )


def test_contact_destination_is_not_public_profile_data(session):
    seed_database(session)
    profile = session.query(Profile).filter_by(slug="jane-doe").one()
    assert hasattr(profile, "contact_configuration")
    assert profile.contact_configuration.to_address
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_schema.py -q`

Expected: FAIL because the database module, models, and seed function do not exist.

- [ ] **Step 3: Implement models and database session setup**

Use UUID/string primary keys, explicit `display_order`, nullable end dates for ongoing records, `is_published` state on public content entities, profile-scoped foreign keys, unique profile slugs, and created/updated timestamps. Keep `ContactConfiguration.to_address` separate from public profile fields.

- [ ] **Step 4: Add Alembic migration and seed command**

Create the initial migration for all tables and a deterministic seed profile containing summary, at least one current and one completed experience, education, grouped skills, concise projects, and a contact configuration loaded from environment variables. Add a CLI entry point or `python -m app.seed` command that is safe to run repeatedly.

- [ ] **Step 5: Run schema tests and migration checks**

Run: `alembic upgrade head && pytest tests/test_schema.py -q`

Expected: migration succeeds and all schema tests pass.

- [ ] **Step 6: Commit**

```bash
git add app/db.py app/models.py app/seed.py alembic.ini migrations tests/test_schema.py
git commit -m "feat: add structured resume database schema"
```

**Done looks like:** SQLite can be migrated from empty to the complete profile schema, and seed data produces one deterministic published profile with ordered resume content and a server-only contact destination.

**How to check:** Delete the local SQLite file, run `alembic upgrade head`, run the seed command twice, and run `pytest tests/test_schema.py -q`; the second seed run must not duplicate records.

### Task 3: Implement the published-content repository and public-safe DTOs

**Files:**
- Create: `app/domain/public_profile.py`
- Create: `app/repositories/public_profile.py`
- Create: `tests/repositories/test_public_profile.py`

**Interfaces:**
- Produces `PublishedProfile` and nested immutable public DTOs without contact destination fields.
- Produces `get_published_profile(session: Session, slug: str) -> PublishedProfile | None`.
- Produces `serialize_public_profile(profile: PublishedProfile) -> dict[str, object]`.

- [ ] **Step 1: Write repository tests**

```python
def test_repository_excludes_unpublished_children(session):
    profile = make_published_profile(session)
    make_unpublished_experience(session, profile)
    session.commit()

    result = get_published_profile(session, profile.slug)

    assert result is not None
    assert all(item.is_published for item in result.experiences)


def test_serialized_profile_contains_no_contact_destination(session):
    result = get_published_profile(session, "jane-doe")
    payload = serialize_public_profile(result)
    assert "to_address" not in repr(payload)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/repositories/test_public_profile.py -q`

Expected: FAIL because the DTOs and repository function do not exist.

- [ ] **Step 3: Implement the public boundary**

Query only a published profile and published child rows, order each collection explicitly, and map ORM objects into DTOs that omit `ContactConfiguration`. Return `None` for missing or unpublished profiles. Ensure serialized data contains only public fields.

- [ ] **Step 4: Run repository tests**

Run: `pytest tests/repositories/test_public_profile.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/domain/public_profile.py app/repositories/public_profile.py tests/repositories/test_public_profile.py
git commit -m "feat: enforce published public profile boundary"
```

**Done looks like:** Every public profile read is filtered to published content, consistently ordered, and represented by a type that cannot include the protected contact destination.

**How to check:** Run the repository tests with unpublished profile, unpublished child, ongoing date, and missing slug fixtures; verify all pass.

### Task 4: Add versioned snapshot generation, validation, and atomic fallback

**Files:**
- Create: `app/snapshots.py`
- Create: `tests/test_snapshots.py`
- Modify: `app/config.py`
- Modify: `app/main.py`

**Interfaces:**
- Produces `write_snapshot(snapshot_dir: Path, profile: PublishedProfile) -> Path`.
- Produces `read_latest_snapshot(snapshot_dir: Path, slug: str) -> PublishedProfile | None`.
- Produces `load_profile_with_fallback(slug: str, db_loader: Callable[[], PublishedProfile | None], snapshot_dir: Path) -> tuple[PublishedProfile | None, str]`.
- Uses source values `"database"` and `"snapshot"` in the returned tuple.

- [ ] **Step 1: Write fallback and atomicity tests**

```python
def test_database_failure_serves_last_known_good_snapshot(tmp_path, profile):
    write_snapshot(tmp_path, profile)

    result, source = load_profile_with_fallback(
        "jane-doe",
        db_loader=lambda: (_ for _ in ()).throw(ConnectionError("sqlite down")),
        snapshot_dir=tmp_path,
    )

    assert source == "snapshot"
    assert result.slug == "jane-doe"


def test_invalid_snapshot_does_not_replace_valid_snapshot(tmp_path, profile):
    valid_path = write_snapshot(tmp_path, profile)
    invalid_path = tmp_path / "jane-doe-v999.json"
    invalid_path.write_text('{"slug":"jane-doe","experiences":null}')

    assert read_latest_snapshot(tmp_path, "jane-doe").slug == "jane-doe"
    assert valid_path.exists()
    assert read_latest_snapshot(tmp_path, "jane-doe").slug == profile.slug
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_snapshots.py -q`

Expected: FAIL because snapshot functions do not exist.

- [ ] **Step 3: Implement validated versioned snapshots**

Serialize only the public DTO. Validate required fields and nested collection shapes with Pydantic before writing. Write to a uniquely named temporary file in the snapshot directory, flush and `fsync`, then atomically replace the active version pointer/file. Keep the prior valid snapshot when generation or validation fails. Read only complete validated files and select the newest valid version for the requested slug.

- [ ] **Step 4: Implement database-first fallback**

Catch only the repository/database availability exceptions needed to trigger fallback, log the failure without secrets, and return the snapshot source. Do not use a snapshot when the database successfully reports a missing or unpublished profile; that remains a deliberate not-found result.

- [ ] **Step 5: Run snapshot tests**

Run: `pytest tests/test_snapshots.py -q`

Expected: PASS, including database failure, malformed snapshot, partial-write, and no-valid-source cases.

- [ ] **Step 6: Commit**

```bash
git add app/snapshots.py app/config.py app/main.py tests/test_snapshots.py
git commit -m "feat: add resilient public profile snapshots"
```

**Done looks like:** A validated, public-only snapshot is versioned and atomically replaceable; a database outage serves the latest valid snapshot; malformed or partial snapshots never replace it.

**How to check:** Run `pytest tests/test_snapshots.py -q`, then manually rename/remove the SQLite file while the snapshot exists and request the profile route; the resume must still render.

### Task 5: Render the public resume page and SEO metadata

**Files:**
- Create: `app/routes/profile.py`
- Create: `templates/profile.html`
- Create: `templates/partials/experience.html`
- Create: `templates/partials/education.html`
- Create: `templates/partials/skills.html`
- Create: `templates/partials/projects.html`
- Create: `templates/errors/not-found.html`
- Create: `tests/routes/test_profile.py`
- Modify: `app/main.py`
- Modify: `static/css/site.css`

**Interfaces:**
- Produces `GET /` and `GET /profiles/{slug}` HTML routes.
- Uses `load_profile_with_fallback()` and passes `profile_source` to the template.

- [ ] **Step 1: Write route tests**

```python
def test_published_profile_renders_all_sections(client, seeded_database):
    response = client.get("/profiles/jane-doe")
    assert response.status_code == 200
    assert "Professional Summary" in response.text
    assert "Experience" in response.text
    assert "Education" in response.text
    assert "Skills" in response.text
    assert "Projects" in response.text
    assert "to_address" not in response.text


def test_missing_profile_returns_not_found(client):
    response = client.get("/profiles/missing")
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/routes/test_profile.py -q`

Expected: FAIL because the profile routes and templates do not exist.

- [ ] **Step 3: Implement route and templates**

Render the profile through semantic `header`, `main`, `section`, and `footer` landmarks. Use stable heading hierarchy, explicit empty states, ordered content, accessible link text, responsive plain CSS, and title/description/Open Graph metadata. Keep the contact destination out of template context.

- [ ] **Step 4: Add not-found and service-unavailable behavior**

Return the not-found template when the database says the slug is missing or unpublished. Return the service-unavailable template only when both the database and snapshot are unavailable. Do not render an empty success page.

- [ ] **Step 5: Run route and accessibility checks**

Run: `pytest tests/routes/test_profile.py -q`

Expected: PASS. Then run the documented local server smoke test and inspect the page at desktop and mobile widths using keyboard-only navigation.

- [ ] **Step 6: Commit**

```bash
git add app/routes/profile.py app/main.py templates/profile.html templates/partials templates/errors static/css/site.css tests/routes/test_profile.py
git commit -m "feat: render public resume profile"
```

**Done looks like:** A recruiter can load the public profile and scan summary, experience, education, skills, projects, and contact action on mobile or desktop, with correct not-found and outage behavior.

**How to check:** Run route tests, start Uvicorn, visit `/profiles/jane-doe`, tab through every control, and confirm the page contains no raw contact destination.

### Task 6: Implement the protected Resend contact form

**Files:**
- Create: `app/contact.py`
- Create: `app/routes/contact.py`
- Create: `templates/partials/contact-form.html`
- Create: `tests/routes/test_contact.py`
- Modify: `app/main.py`
- Modify: `templates/profile.html`

**Interfaces:**
- Produces `ContactMessage` validation model with `name`, `email`, `message`, and `honeypot`.
- Produces `ContactSender.send(message: ContactMessage) -> None`.
- Produces `POST /contact` returning generic success or failure status without destination data.

- [ ] **Step 1: Write contact validation and provider tests**

```python
def test_invalid_contact_is_rejected_without_provider_call(client, mock_resend):
    response = client.post(
        "/contact",
        data={"name": "A", "email": "not-an-email", "message": "Hello", "honeypot": ""},
    )
    assert response.status_code == 422
    mock_resend.assert_not_called()


def test_provider_failure_is_not_reported_as_success(client, mock_resend):
    mock_resend.side_effect = RuntimeError("provider unavailable")
    response = client.post(
        "/contact",
        data={"name": "A", "email": "a@example.com", "message": "Hello", "honeypot": ""},
    )
    assert response.status_code == 502
    assert "to_address" not in response.text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/routes/test_contact.py -q`

Expected: FAIL because contact validation, sender, and route do not exist.

- [ ] **Step 3: Implement validation, honeypot, and rate limiting**

Reject invalid email addresses, blank/oversized fields, and non-empty honeypot submissions. Add an in-memory per-IP rate limiter suitable for local Codespaces, with a small configurable window and limit. Keep provider credentials and `contact_to` server-side.

- [ ] **Step 4: Implement Resend delivery**

Construct a plain-text message from validated fields, call Resend using the configured API key/from/to settings, log only request identifiers and failure categories, and return a generic success only after the provider confirms acceptance. Never include the destination in HTML or JSON responses.

- [ ] **Step 5: Run contact tests**

Run: `pytest tests/routes/test_contact.py -q`

Expected: PASS, including invalid input, honeypot, rate limit, provider success, provider failure, and no-destination-leak checks.

- [ ] **Step 6: Commit**

```bash
git add app/contact.py app/routes/contact.py templates/partials/contact-form.html tests/routes/test_contact.py app/main.py templates/profile.html
git commit -m "feat: add protected Resend contact form"
```

**Done looks like:** Visitors can submit a validated contact message without seeing the destination address; Resend failures are surfaced as failures and abuse controls prevent repeated submissions.

**How to check:** Run contact tests with Resend mocked; in Codespaces, configure test credentials only in environment variables and send one test message, confirming no destination appears in page source, logs, or response.

### Task 7: Generate snapshots from seeded public content and document operations

**Files:**
- Create: `app/generate_snapshot.py`
- Create: `tests/test_snapshot_command.py`
- Modify: `README.md`
- Modify: `.gitignore`

**Interfaces:**
- Produces `python -m app.generate_snapshot --slug jane-doe`.
- Reads SQLite through the same public repository and writes to `SNAPSHOT_DIR`.

- [ ] **Step 1: Write command test**

```python
def test_snapshot_command_writes_public_snapshot(tmp_path, seeded_database, monkeypatch):
    monkeypatch.setenv("SNAPSHOT_DIR", str(tmp_path))
    run_snapshot_command(["--slug", "jane-doe"])
    files = list(tmp_path.glob("*.json"))
    assert files
    assert "to_address" not in files[0].read_text()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_snapshot_command.py -q`

Expected: FAIL because the command does not exist.

- [ ] **Step 3: Implement the command**

Load the selected published profile through `get_published_profile()`, fail with a nonzero exit code for missing/unpublished profiles, validate and atomically write the snapshot, and print only the slug, version, and outcome.

- [ ] **Step 4: Document recovery and local operation**

Document migration, seeding, snapshot generation after content changes, starting Uvicorn, configuring Resend, simulating database outage, and restoring SQLite. Add snapshot runtime files and local databases to `.gitignore`; keep a checked-in seed/migration source of truth.

- [ ] **Step 5: Run command and operations checks**

Run: `pytest tests/test_snapshot_command.py -q && python -m app.generate_snapshot --slug jane-doe`

Expected: PASS and a validated snapshot file appears in `SNAPSHOT_DIR`.

- [ ] **Step 6: Commit**

```bash
git add app/generate_snapshot.py tests/test_snapshot_command.py README.md .gitignore
git commit -m "docs: document profile snapshot operations"
```

**Done looks like:** A content update can be migrated, seeded, and converted into a public-safe snapshot using one documented command, and local outage recovery is reproducible.

**How to check:** Follow the README from an empty workspace through migration, seed, snapshot generation, server start, and database outage simulation; run the command test.

### Task 8: Run the complete verification suite and review production behavior

**Files:**
- Modify: `README.md` only if verification exposes inaccurate instructions.
- Test: `tests/` entire suite.

- [ ] **Step 1: Run formatting, type, test, and build checks**

Run:

```bash
ruff check .
ruff format --check .
mypy app
pytest -q
```

Expected: all commands exit successfully.

- [ ] **Step 2: Run the end-to-end local smoke test**

Run:

```bash
alembic upgrade head
python -m app.seed
python -m app.generate_snapshot --slug jane-doe
uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

Check `/healthz`, `/profiles/jane-doe`, a missing profile, contact validation, and the database-outage snapshot fallback.

- [ ] **Step 3: Perform the final privacy and accessibility review**

Confirm raw contact destination is absent from rendered HTML, serialized public data, snapshots, logs, and error responses. Confirm keyboard navigation, focus visibility, heading order, link names, responsive layout, and service-unavailable behavior.

- [ ] **Step 4: Commit verification-only fixes if needed**

```bash
git add README.md
git commit -m "test: verify resume platform end to end"
```

Only commit this step if documentation corrections are required; do not add unrelated refactors.

**Done looks like:** The complete test/type/format suite passes, the local Codespaces workflow is documented and reproducible, the profile survives database outage through the snapshot, and privacy/accessibility checks pass.

**How to check:** Run the commands above from a clean working tree and record the successful output in the pull request or handoff.
