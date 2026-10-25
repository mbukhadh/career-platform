import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.contact import ContactSender, RateLimiter
from app.db import get_session_factory
from app.domain.public_profile import PublicProject
from app.repositories.public_profile import get_published_projects
from app.routes.contact import router as contact_router
from app.routes.profile import router as profile_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="Career Platform")
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.state.settings = get_settings()
    app.state.templates = Jinja2Templates(directory="templates")
    app.state.templates.env.filters["resume_date"] = _format_resume_date
    app.state.contact_sender = ContactSender(app.state.settings)
    app.state.contact_rate_limiter = RateLimiter()

    def projects_loader(slug: str) -> tuple[PublicProject, ...] | None:
        """Read projects on every request. None means the query failed.

        Each call opens a fresh session and closes it, so a failure is not
        cached and the next request tries the database again.
        """
        try:
            with get_session_factory(app.state.settings)() as session:
                return get_published_projects(session, slug)
        except SQLAlchemyError:
            logger.exception("Projects query failed")
            return None

    app.state.projects_loader = projects_loader
    app.include_router(profile_router)
    app.include_router(contact_router)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


def _format_resume_date(value):
    if value is None:
        return "Present"
    return value.strftime("%b %Y")
