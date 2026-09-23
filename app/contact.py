import re
import time
from dataclasses import dataclass
from threading import Lock

import httpx

from app.config import Settings


@dataclass(frozen=True)
class ContactMessage:
    name: str
    email: str
    message: str
    honeypot: str = ""


class ContactSender:
    def __init__(self, settings: Settings):
        self.settings = settings

    def send(self, message: ContactMessage) -> None:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {self.settings.resend_api_key}"},
            json={
                "from": self.settings.contact_from,
                "to": [self.settings.contact_to],
                "subject": f"Resume contact from {message.name}",
                "text": f"From: {message.name} <{message.email}>\n\n{message.message}",
            },
            timeout=10,
        )
        response.raise_for_status()


class RateLimiter:
    def __init__(self, limit: int = 5, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            recent = [
                timestamp
                for timestamp in self._requests.get(key, [])
                if now - timestamp < self.window_seconds
            ]
            if len(recent) >= self.limit:
                self._requests[key] = recent
                return False
            recent.append(now)
            self._requests[key] = recent
            return True


def validate_contact(
    name: str, email: str, message: str, honeypot: str = ""
) -> ContactMessage:
    if not 1 <= len(name.strip()) <= 120:
        raise ValueError("invalid name")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
        raise ValueError("invalid email")
    if not 1 <= len(message.strip()) <= 5000:
        raise ValueError("invalid message")
    if honeypot.strip():
        raise ValueError("spam detected")
    return ContactMessage(name.strip(), email.strip(), message.strip(), "")
