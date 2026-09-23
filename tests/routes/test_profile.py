from fastapi.testclient import TestClient

from app.domain.public_profile import PublishedProfile
from app.main import create_app


def client():
    app = create_app()
    app.state.profile_loader = lambda slug: (
        PublishedProfile(
            slug="jane-doe",
            name="Jane Doe",
            headline="Engineer",
            summary="Professional Summary",
            location="Codespaces",
        ),
        "database",
    )
    return TestClient(app)


def test_published_profile_renders_all_sections():
    response = client().get("/profiles/jane-doe")
    assert response.status_code == 200
    assert "Professional Summary" in response.text
    assert "Experience" in response.text
    assert "Education" in response.text
    assert "Skills" in response.text
    assert "Projects" in response.text
    assert "to_address" not in response.text


def test_missing_profile_returns_not_found():
    app = create_app()
    app.state.profile_loader = lambda slug: (None, "database")
    response = TestClient(app).get("/profiles/missing")
    assert response.status_code == 404
