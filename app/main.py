from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.contact import ContactSender, RateLimiter
from app.db import get_session_factory
from app.repositories.public_profile import get_published_profile
from app.routes.contact import router as contact_router
from app.routes.profile import router as profile_router
from app.snapshots import load_profile_with_fallback


def create_app() -> FastAPI:
    app = FastAPI(title="Career Platform")
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.state.settings = get_settings()
    app.state.templates = Jinja2Templates(directory="templates")
    app.state.contact_sender = ContactSender(app.state.settings)
    app.state.contact_rate_limiter = RateLimiter()

    def profile_loader(slug: str):
        settings = app.state.settings

        def load_from_database():
            with get_session_factory(settings)() as session:
                return get_published_profile(session, slug)

        profile, source = load_profile_with_fallback(
            slug, load_from_database, settings.snapshot_dir
        )
        if profile is None and source == "snapshot":
            return None, "snapshot-error"
        return profile, source

    app.state.profile_loader = profile_loader
    app.include_router(profile_router)
    app.include_router(contact_router)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app
