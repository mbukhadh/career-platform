from fastapi.testclient import TestClient

from app.main import create_app


def client():
    app = create_app()
    app.state.projects_loader = lambda slug: ()
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
    response = TestClient(create_app()).get("/profiles/missing")
    assert response.status_code == 404


def test_profile_footer_links_to_privacy_page():
    response = client().get("/")
    assert '<a href="/privacy">Privacy</a>' in response.text


def test_privacy_page_renders_without_database():
    response = TestClient(create_app()).get("/privacy")
    assert response.status_code == 200
    assert "<h1>Privacy</h1>" in response.text
    assert "_ga_SE674YJENK" in response.text


GTAG_SCRIPT_URL = "googletagmanager.com/gtag/js"


def test_pages_do_not_contain_the_google_tag_script_url():
    pages = [
        client().get("/"),
        TestClient(create_app()).get("/privacy"),
        TestClient(create_app()).get("/profiles/missing"),
    ]
    for response in pages:
        assert GTAG_SCRIPT_URL not in response.text


def test_pages_include_consent_banner_and_cookie_settings_link():
    for response in (client().get("/"), TestClient(create_app()).get("/privacy")):
        assert 'id="consent-banner"' in response.text
        assert 'data-consent="accepted"' in response.text
        assert 'data-consent="declined"' in response.text
        assert "data-cookie-settings>Cookie settings</a>" in response.text
        assert "js/consent.js" in response.text


def test_consent_script_is_served():
    response = TestClient(create_app()).get("/static/js/consent.js")
    assert response.status_code == 200
    assert "analytics-consent" in response.text
