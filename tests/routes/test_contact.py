from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.main import create_app


def test_invalid_contact_is_rejected_without_provider_call():
    app = create_app()
    sender = Mock()
    app.state.contact_sender = sender
    response = TestClient(app).post(
        "/contact",
        data={"name": "A", "email": "not-an-email", "message": "Hello", "honeypot": ""},
    )
    assert response.status_code == 422
    sender.assert_not_called()


def test_provider_failure_is_not_reported_as_success():
    app = create_app()
    sender = Mock()
    sender.send.side_effect = RuntimeError("provider unavailable")
    app.state.contact_sender = sender
    response = TestClient(app).post(
        "/contact",
        data={
            "name": "A",
            "email": "a@example.com",
            "message": "Hello",
            "honeypot": "",
        },
    )
    assert response.status_code == 502
    assert "to_address" not in response.text
