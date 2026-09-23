import logging

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from app.contact import validate_contact

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/contact", response_class=HTMLResponse)
def contact(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
    honeypot: str = Form(""),
) -> HTMLResponse:
    try:
        contact_message = validate_contact(name, email, message, honeypot)
    except ValueError as error:
        return HTMLResponse(str(error), status_code=422)

    client_host = request.client.host if request.client else "unknown"
    if not request.app.state.contact_rate_limiter.allow(client_host):
        return HTMLResponse(
            "Too many requests. Please try again later.", status_code=429
        )
    try:
        request.app.state.contact_sender.send(contact_message)
    except Exception:
        logger.exception("Contact provider failure")
        return HTMLResponse(
            "Unable to send your message right now. Please try again later.",
            status_code=502,
        )
    return HTMLResponse("Your message was sent.", status_code=200)
