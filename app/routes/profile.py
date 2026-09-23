from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.domain.public_profile import PublishedProfile

router = APIRouter()


def _render(request: Request, profile: PublishedProfile, source: str) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={"profile": profile, "profile_source": source},
    )


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return profile_page(request, "jane-doe")


@router.get("/profiles/{slug}", response_class=HTMLResponse)
def profile_page(request: Request, slug: str) -> HTMLResponse:
    loader = getattr(request.app.state, "profile_loader", lambda _: (None, "database"))
    profile, source = loader(slug)
    if profile is None:
        template = (
            "errors/service-unavailable.html"
            if source == "snapshot-error"
            else "errors/not-found.html"
        )
        status_code = 503 if source == "snapshot-error" else 404
        return request.app.state.templates.TemplateResponse(
            request=request,
            name=template,
            context={},
            status_code=status_code,
        )
    return _render(request, profile, source)
