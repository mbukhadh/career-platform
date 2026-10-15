from datetime import date

from fastapi.testclient import TestClient

from app.domain.public_profile import (
    PublicEducation,
    PublicExperience,
    PublicSkill,
    PublicSkillGroup,
    PublishedProfile,
)
from app.main import create_app


def client():
    app = create_app()
    app.state.profile_loader = lambda slug: (
        PublishedProfile(
            slug="mj-bukhadhour",
            name="Mohammad (MJ) Bukhadhour",
            headline="Engineer",
            summary="Professional Summary",
            location="Codespaces",
            experiences=(
                PublicExperience(
                    employer="",
                    title="Experience — coming soon",
                    start_date=None,
                    end_date=None,
                    location=None,
                    summary="",
                    display_order=0,
                ),
            ),
            education=(
                PublicEducation(
                    institution="Loyola Marymount University",
                    program="B.S. Information Systems & Business Analytics",
                    start_date=None,
                    end_date=date(2027, 5, 31),
                    details=None,
                    display_order=0,
                ),
            ),
            skill_groups=(
                PublicSkillGroup(
                    name="Programming & Data",
                    display_order=0,
                    skills=(
                        PublicSkill(name="Python", display_order=0),
                        PublicSkill(name="SQL", display_order=1),
                    ),
                ),
            ),
        ),
        "database",
    )
    return TestClient(app)


def test_published_profile_renders_all_sections():
    response = client().get("/profiles/mj-bukhadhour")
    assert response.status_code == 200
    assert "Professional Summary" in response.text
    assert "Experience" in response.text
    assert "Education" in response.text
    assert "Skills" in response.text
    assert "Projects" in response.text
    assert "to_address" not in response.text
    assert "<h3>Experience — coming soon</h3>" in response.text
    assert "Professional experience details coming soon." not in response.text
    assert "Jan 2026" not in response.text
    assert "Expected May 2027" in response.text
    assert "Programming &amp; Data" in response.text
    assert "<h3>Tools</h3>" not in response.text


def test_missing_profile_returns_not_found():
    app = create_app()
    app.state.profile_loader = lambda slug: (None, "database")
    response = TestClient(app).get("/profiles/missing")
    assert response.status_code == 404


def test_profile_footer_links_to_privacy_page():
    response = client().get("/")
    assert '<a href="/privacy">Privacy</a>' in response.text


def test_privacy_page_renders_without_database():
    response = TestClient(create_app()).get("/privacy")
    assert response.status_code == 200
    assert "<h1>Privacy</h1>" in response.text
    assert "_ga_SE674YJENK" in response.text
