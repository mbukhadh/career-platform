from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings


def create_app() -> FastAPI:
    app = FastAPI(title="Career Platform")
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.state.settings = get_settings()
    app.state.templates = Jinja2Templates(directory="templates")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app
