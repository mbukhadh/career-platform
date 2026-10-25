from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.profile_content import PROFILE

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return profile_page(request, PROFILE.slug)


@router.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse(
        request=request, name="privacy.html", context={}
    )


@router.get("/profiles/{slug}", response_class=HTMLResponse)
def profile_page(request: Request, slug: str) -> HTMLResponse:
    templates = request.app.state.templates
    if slug != PROFILE.slug:
        return templates.TemplateResponse(
            request=request, name="errors/not-found.html", context={}, status_code=404
        )
    # None means the projects query failed: keep the profile, say so, return 503.
    projects = request.app.state.projects_loader(slug)
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={"profile": PROFILE, "projects": projects},
        status_code=200 if projects is not None else 503,
    )
