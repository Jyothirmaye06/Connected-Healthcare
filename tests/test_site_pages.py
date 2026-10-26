from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.authentication import create_password_hash

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def configured_account(role, hospital_ids=()):
    salt, password_hash = create_password_hash("demonstration-password-long-enough")
    return {
        "role": role,
        "hospital_ids": list(hospital_ids),
        "password_salt": salt,
        "password_hash": password_hash,
    }


def test_anonymous_home_and_language_switch():
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py"))
    app.session_state["language"] = "te"
    app.run()

    assert not app.exception
    assert "ఆరోగ్య సమాచారాన్ని" in app.title[0].value
    assert len(app.get("page_link")) >= 3


def test_anonymous_public_health_page_loads_without_database_writes():
    app = AppTest.from_file(str(PROJECT_ROOT / "src" / "ui" / "pages" / "public_health.py")).run()

    assert not app.exception
    assert app.title[0].value == "Public Health"
    assert any("does not diagnose" in item.value for item in app.warning)


def test_public_health_labels_follow_selected_language():
    app = AppTest.from_file(str(PROJECT_ROOT / "src" / "ui" / "pages" / "public_health.py"))
    app.session_state["language"] = "hi"
    app.run()

    assert not app.exception
    assert app.title[0].value == "सार्वजनिक स्वास्थ्य"


def test_anonymous_hospital_page_loads_and_labels_forecasts():
    app = AppTest.from_file(str(PROJECT_ROOT / "src" / "ui" / "pages" / "hospitals.py")).run(timeout=30)

    assert not app.exception
    assert app.title[0].value == "Hospital Information"
    assert any("no verified live feed" in item.value for item in app.info)


def test_unauthorized_staff_page_denies_access():
    app = AppTest.from_file(str(PROJECT_ROOT / "src" / "ui" / "pages" / "staff.py")).run()

    assert not app.exception
    assert any("Access denied" in item.value for item in app.error)


def test_authorized_staff_page_is_available_for_configured_user():
    app = AppTest.from_file(str(PROJECT_ROOT / "src" / "ui" / "pages" / "staff.py"))
    app.secrets["users"] = {"staffer": configured_account("staff", [1])}
    app.session_state["authenticated_username"] = "staffer"
    app.run()

    assert not app.exception
    assert app.title[0].value == "Staff Portal"
    assert app.number_input


def test_unauthorized_admin_page_denies_access():
    app = AppTest.from_file(str(PROJECT_ROOT / "src" / "ui" / "pages" / "admin.py")).run()

    assert not app.exception
    assert any("Access denied" in item.value for item in app.error)


def test_configured_admin_can_open_technical_dashboard():
    app = AppTest.from_file(str(PROJECT_ROOT / "src" / "ui" / "pages" / "admin.py"))
    app.secrets["users"] = {"administrator": configured_account("admin")}
    app.session_state["authenticated_username"] = "administrator"
    app.run(timeout=60)

    assert not app.exception
    assert app.title[0].value == "AI & System Intelligence"
    assert len(app.tabs) == 7


def test_login_page_rejects_invalid_credentials():
    app = AppTest.from_file(str(PROJECT_ROOT / "src" / "ui" / "pages" / "login.py"))
    app.secrets["users"] = {"staffer": configured_account("staff", [1])}
    app.run()
    app.text_input[0].set_value("staffer")
    app.text_input[1].set_value("wrong-password")
    app.button[0].click().run()

    assert any("Sign-in failed" in item.value for item in app.error)
